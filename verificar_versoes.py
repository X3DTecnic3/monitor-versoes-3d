import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    PLAYWRIGHT_DISPONIVEL = False

FONTES = [
    {
        "id": "exscan-trak",
        "nome": "EXScan Trak",
        "fabricante": "Shining 3D / EinScan",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001647097-download-exscan-trak-software",
        "usar_browser": False,
    },
    {
        "id": "exscan-rigil",
        "nome": "EXScan Rigil Desktop",
        "fabricante": "Shining 3D / EinScan",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001589102-download-exscan-rigil-desktop-software-for-einscan-rigil-series-",
        "usar_browser": False,
    },
    {
        "id": "geomagic-design-x",
        "nome": "Geomagic Design X",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/GeomagicDesignX?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-control-x",
        "nome": "Geomagic Control X",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-Control-X?language=en_US",
        "usar_browser": True,
    },
]

VERSOES_FILE = Path("versoes.json")
DIAS_AVISO = 7

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Apanha versões como 2026.1.0, 1.0.2.3 ou 1.4.0-37
VERSION_REGEX = re.compile(
    r"\bv?\d+\.\d+(?:\.\d+){0,3}(?:-[A-Za-z0-9._-]+)?\b",
    re.IGNORECASE,
)


def normalizar_linhas(texto_bruto: str) -> str:
    linhas = [linha.strip() for linha in texto_bruto.splitlines() if linha.strip()]
    return "\n".join(linhas)


def obter_html_requests(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def extrair_texto_util(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    contentor = (
        soup.select_one(".article-body")
        or soup.select_one("[data-testid='article-body']")
        or soup.select_one("c-knowledge-article-view")
        or soup.select_one(".forceCommunityRichText")
        or soup.select_one("main")
        or soup.select_one("article")
        or soup.body
    )

    texto = contentor.get_text("\n") if contentor else soup.get_text("\n")
    return normalizar_linhas(texto)


def ler_texto_playwright(url: str) -> str:
    if not PLAYWRIGHT_DISPONIVEL:
        raise RuntimeError(
            "Playwright não está instalado. Corre: python -m pip install playwright && python -m playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        texto_visivel = ""
        tamanho_anterior = 0
        estavel_contagem = 0

        for _ in range(25):
            page.wait_for_timeout(1000)
            candidato = normalizar_linhas(page.inner_text("body"))
            texto_visivel = candidato

            linhas_lower = [l.lower() for l in candidato.splitlines()]
            tem_corpo_util = len(candidato) > 700 and "loading" not in linhas_lower[-3:]
            tem_versao = bool(VERSION_REGEX.search(candidato))

            if len(candidato) == tamanho_anterior and len(candidato) > 400:
                estavel_contagem += 1
            else:
                estavel_contagem = 0
            tamanho_anterior = len(candidato)

            if (tem_versao and estavel_contagem >= 2) or (tem_corpo_util and estavel_contagem >= 3):
                break

        browser.close()
        return texto_visivel


def escolher_versao_principal(texto: str) -> tuple[str | None, list[str]]:
    linhas = texto.splitlines()
    candidatas_ordenadas = []

    for linha in linhas:
        if re.search(r"\b(version|ver\.?|release|download|update)\b", linha, re.IGNORECASE):
            for match in VERSION_REGEX.findall(linha):
                if match not in candidatas_ordenadas:
                    candidatas_ordenadas.append(match)

    for match in VERSION_REGEX.findall(texto):
        if match not in candidatas_ordenadas:
            candidatas_ordenadas.append(match)

    versao_principal = candidatas_ordenadas[0] if candidatas_ordenadas else None
    return versao_principal, candidatas_ordenadas[:10]


def imprimir_diagnostico_sem_versao(texto: str) -> None:
    linhas = texto.splitlines()
    print("  [DIAGNÓSTICO] Nenhuma versão detetada. Primeiras linhas visíveis:")
    for linha in linhas[:10]:
        print(f"    | {linha[:120]}")
    if not linhas:
        print("    | (Texto vazio devolvido pela página)")


def aviso_ainda_valido(data_iso: str | None, agora: datetime, dias: int = DIAS_AVISO) -> bool:
    if not data_iso:
        return False
    try:
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (agora - dt) < timedelta(days=dias)
    except ValueError:
        return False


def carregar_dados_anteriores() -> dict:
    if VERSOES_FILE.exists():
        dados = json.loads(VERSOES_FILE.read_text(encoding="utf-8"))
        return {item["id"]: item for item in dados.get("softwares", [])}
    return {}


def main() -> None:
    anteriores_por_id = carregar_dados_anteriores()
    agora_dt = datetime.now(timezone.utc)
    agora_iso = agora_dt.isoformat()
    resultado_softwares = []

    for fonte in FONTES:
        fid = fonte["id"]
        anterior = anteriores_por_id.get(fid, {})
        print(f"\nA verificar [{fonte['fabricante']}] {fonte['nome']}...")

        try:
            if fonte.get("usar_browser"):
                texto = ler_texto_playwright(fonte["url"])
            else:
                html = obter_html_requests(fonte["url"])
                texto_teste = extrair_texto_util(html)
                if len(texto_teste) < 150 and PLAYWRIGHT_DISPONIVEL:
                    print("  [INFO] Pouco texto no HTML estático; a tentar com Playwright...")
                    texto = ler_texto_playwright(fonte["url"])
                else:
                    texto = texto_teste

            versao_atual, candidatas = escolher_versao_principal(texto)
            hash_texto = hashlib.sha256(texto.encode("utf-8")).hexdigest()

        except Exception as exc:
            print(f"  [ERRO] {exc}")
            if anterior:
                anterior["ultimo_erro"] = str(exc)
                anterior["ultima_verificacao"] = agora_iso
                resultado_softwares.append(anterior)
            continue

        if versao_atual is None:
            imprimir_diagnostico_sem_versao(texto)

        versao_anterior = anterior.get("versao_atual")
        historico = list(anterior.get("historico_versoes", []))

        if versao_atual and versao_atual not in historico:
            historico.insert(0, versao_atual)

        if versao_anterior is None and versao_atual is not None:
            nova_versao = True
            data_atualizacao = anterior.get("data_ultima_atualizacao") or agora_iso
            print(f"  [INICIAL] Versão detetada: {versao_atual}")
        elif versao_atual and versao_atual != versao_anterior:
            nova_versao = True
            data_atualizacao = agora_iso
            print(f"  [NOVA VERSÃO!] {versao_anterior} -> {versao_atual}")
        else:
            data_atualizacao = anterior.get("data_ultima_atualizacao")
            aviso_anterior = bool(anterior.get("nova_versao", False))
            nova_versao = aviso_anterior and aviso_ainda_valido(data_atualizacao, agora_dt, DIAS_AVISO)
            if aviso_anterior and not nova_versao:
                print(f"  [AVISO EXPIRADO] Passaram mais de {DIAS_AVISO} dias desde a última atualização.")
            else:
                print(f"  [SEM MUDANÇA DE VERSÃO] Atual: {versao_atual} | Candidatas: {candidatas}")

        resultado_softwares.append({
            "id": fid,
            "nome": fonte["nome"],
            "fabricante": fonte["fabricante"],
            "url": fonte["url"],
            "versao_atual": versao_atual,
            "versoes_candidatas": candidatas,
            "historico_versoes": historico[:10],
            "hash_conteudo": hash_texto,
            "nova_versao": nova_versao,
            "data_ultima_atualizacao": data_atualizacao,
            "ultima_verificacao": agora_iso,
        })

    payload = {
        "atualizado_em": agora_iso,
        "softwares": resultado_softwares,
    }
    VERSOES_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nFicheiro '{VERSOES_FILE.resolve()}' atualizado com sucesso.")


if __name__ == "__main__":
    main()