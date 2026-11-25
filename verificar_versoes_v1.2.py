import hashlib
import json
import re
import sys
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
# --- Shining 3D (EinScan / FreeScan / EinStar) ---
    {
        "id": "exscan-trak",
        "nome": "EXScan Trak",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001647097-download-exscan-trak-software",
        "usar_browser": False,
    },
    {
        "id": "exscan-rigil",
        "nome": "EXScan Rigil Desktop",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001589102-download-exscan-rigil-desktop-software-for-einscan-rigil-series-",
        "usar_browser": False,
    },
    {
        "id": "exmodel",
        "nome": "EXModel",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001285793-latest-software-download-for-exmodel",
        "usar_browser": False,
    },
    {
        "id": "exscan-libre-pc",
        "nome": "EXScan Libre PC (EinScan Libre)",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001485101-download-exscan-libre-pc-software-for-einscan-libre-",
        "usar_browser": False,
    },
    {
        "id": "einscan-se-sp-v2",
        "nome": "EinScan SE / SP / SE V2 / SP V2",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000998873-the-latest-software-for-einscan-se-sp-se-v2-sp-v2",
        "usar_browser": False,
    },
    {
        "id": "einscan-h-h2",
        "nome": "EinScan H / H2",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000999739-the-latest-software-for-einscan-h-h2",
        "usar_browser": False,
    },
    {
        "id": "einscan-hx-hx2",
        "nome": "EinScan HX / HX2",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000999741-the-latest-software-for-einscan-hx-hx2",
        "usar_browser": False,
        "ignorar_versoes": ["5.0"],
    },
    {
        "id": "einscan-pro-2x-v2-pro-hd",
        "nome": "EinScan Pro 2X V2 / Pro HD",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001048840-the-latest-software-for-einscan-pro-2x-v2-pro-hd",
        "usar_browser": False,
    },
    {
        "id": "einscan-pro-pro-plus",
        "nome": "EinScan Pro / Pro+",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000999743-the-latest-software-for-einscan-pro-pro-plus",
        "usar_browser": False,
    },
    {
        "id": "einscan-pro-2x-pro-2x-plus",
        "nome": "EinScan Pro 2X / Pro 2X+",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000999742-the-latest-software-for-einscan-pro-2x-pro-2x-plus",
        "usar_browser": False,
    },
    {
        "id": "transcan-c",
        "nome": "Transcan-C",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60000999734-the-latest-software-for-transcan-c",
        "usar_browser": False,
    },
    {
        "id": "freescan-combo-wireless",
        "nome": "FreeScan Combo / Combo Wireless",
        "fabricante": "Shining 3D",
        "url": "https://support.shining3d.com/en/support/solutions/articles/60001647616-latest-software-download-for-freescan-combo-combo-wireless",
        "usar_browser": False,
    },
    {
        "id": "freescan-handheld",
        "nome": "FreeScan Handheld Scanners",
        "fabricante": "Shining 3D",
        "url": "https://support.shining3d.com/en/support/solutions/articles/60001191260-software-download-for-freescan-handheld-scanners",
        "usar_browser": False,
    },
    {
        "id": "einstar-software",
        "nome": "EinStar Software",
        "fabricante": "Shining 3D",
        "url": "https://support.einstar.com/support/solutions/articles/60000782576-einstar-software-download",
        "usar_browser": False,
    },
    {
        "id": "starvision-pc-einstar-vega",
        "nome": "StarVision PC (EinStar Vega)",
        "fabricante": "Shining 3D",
        "url": "https://support.einstar.com/support/solutions/articles/60001436421-download-starvision-pc-software-for-einstar-vega-",
        "usar_browser": False,
        "ignorar_versoes": ["1.1"],
    },
    {
        "id": "exstar-hub-desktop",
        "nome": "EXStar Hub Desktop (EinStar EZ Go / Rockit / 2)",
        "fabricante": "Shining 3D",
        "url": "https://support.einstar.com/support/solutions/articles/60001635292-download-exstar-hub-desktop-software-for-einstar-ez-go-einstar-rockit-einstar-2-",
        "usar_browser": False,
    },
    {
        "id": "exstar-mobile",
        "nome": "EXStar Mobile (EinStar EZ Go / Rockit / 2)",
        "fabricante": "Shining 3D",
        "url": "https://support.einstar.com/support/solutions/articles/60001648942-download-exstar-mobile-mobile-application-for-einstar-ez-go-einstar-rockit-einstar-2-",
        "usar_browser": False,
    },
    {
        "id": "shining3d-inspect-2026",
        "nome": "Shining 3D Inspect 2026",
        "fabricante": "Shining 3D",
        "url": "https://support.shining3d.com/en/support/solutions/articles/60001645525-software-download-for-shining3d-inspect-2026",
        "usar_browser": False,
    },
    {
        "id": "shining3d-inspect-2026-activation",
        "nome": "Activation Tool for Shining 3D Inspect 2026",
        "fabricante": "Shining 3D",
        "url": "https://support.shining3d.com/en/support/solutions/articles/60001645527-activation-tool-for-shining3d-inspect-2026",
        "usar_browser": False,
    },
    {
        "id": "geomagic-essentials-shining3d",
        "nome": "Geomagic Essentials (Shining 3D)",
        "fabricante": "Shining 3D",
        "url": "https://support.einscan.com/en/support/solutions/articles/60001004958-geomagic-essentials",
        "usar_browser": False,
    },
    # --- 3D Systems ---
    {
        "id": "3d-sprint",
        "nome": "3D Sprint",
        "fabricante": "3D Systems",
        "url": "https://support.3dsystems.com/s/article/3D-Sprint?language=en_US",
        "usar_browser": True,
    },
    # --- Hexagon / Geomagic ---
    {
        "id": "geomagic-for-solidworks",
        "nome": "Geomagic for SOLIDWORKS",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-for-SOLIDWORKS?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-design-x",
        "nome": "Geomagic Design X",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/GeomagicDesignX?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-wrap",
        "nome": "Geomagic Wrap",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-Wrap?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-control-x",
        "nome": "Geomagic Control X",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-Control-X?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-freeform",
        "nome": "Geomagic Freeform",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-Freeform?language=en_US",
        "usar_browser": True,
    },
    {
        "id": "geomagic-sculpt",
        "nome": "Geomagic Sculpt",
        "fabricante": "Hexagon / Geomagic",
        "url": "https://support.geomagic.com/s/article/Geomagic-Sculpt?language=en_US",
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
    r"\b(?:(?:20\d{2}\s+)?(?:v|r)?\s*\d+(?:\.\d+){1,3}(?:-[A-Za-z0-9._-]+)?)\b",
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


TELEFONE_PONTOS_REGEX = re.compile(r"^\d{3,4}\.\d{3,4}\.\d{4}$")


def _parece_telefone(match: str, linha: str) -> bool:
    limpo = match.strip()
    if TELEFONE_PONTOS_REGEX.match(limpo):
        return True
    # Deteta indicativo telefónico imediatamente antes do número (ex.: +1 888.598.1438)
    padrao_indicativo = re.compile(r"\+\d{1,3}\s+" + re.escape(limpo))
    if padrao_indicativo.search(linha):
        return True
    return False


def _versao_deve_ser_ignorada(match: str, ignorar: list[str] | None) -> bool:
    if not ignorar:
        return False
    m = re.sub(r"^20\d{2}\s+", "", match.strip().lower()).lstrip("vr").strip()
    for item in ignorar:
        alvo = re.sub(r"^20\d{2}\s+", "", item.strip().lower()).lstrip("vr").strip()
        if m == alvo or m.startswith(alvo + "."):
            return True
    return False


def escolher_versao_principal(
    texto: str, ignorar: list[str] | None = None
) -> tuple[str | None, list[str]]:
    linhas = texto.splitlines()
    candidatas_linhas_chave = []
    candidatas_restantes = []

    for linha in linhas:
        eh_linha_chave = bool(
            re.search(r"\b(version|ver\.?|release|download|update)\b", linha, re.IGNORECASE)
        )
        for match in VERSION_REGEX.findall(linha):
            limpo = match.strip()
            if _parece_telefone(limpo, linha) or _versao_deve_ser_ignorada(limpo, ignorar):
                continue
            if eh_linha_chave:
                if limpo not in candidatas_linhas_chave:
                    candidatas_linhas_chave.append(limpo)
            else:
                if limpo not in candidatas_restantes:
                    candidatas_restantes.append(limpo)

    candidatas_ordenadas = list(candidatas_linhas_chave)
    for c in candidatas_restantes:
        if c not in candidatas_ordenadas:
            candidatas_ordenadas.append(c)

    versao_principal = candidatas_ordenadas[0] if candidatas_ordenadas else None

    # Só substitui versões curtas de 1 ponto se NÃO começarem por ano (4 dígitos, como 2026.4)
    if versao_principal and versao_principal.count(".") == 1:
        primeiro_bloco = versao_principal.lstrip("vVrR").strip().split(".")[0]
        if len(primeiro_bloco) < 4:
            mais_especifica = next(
                (c for c in candidatas_ordenadas if c.count(".") >= 2),
                None,
            )
            if mais_especifica:
                versao_principal = mais_especifica

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
    ocorreram_falhas = False

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

            versao_atual, candidatas = escolher_versao_principal(texto, fonte.get("ignorar_versoes"))
            hash_texto = hashlib.sha256(texto.encode("utf-8")).hexdigest()

        except Exception as exc:
            ocorreram_falhas = True
            print(f"  [ERRO] {exc}")
            if anterior:
                item_erro = dict(anterior)
                item_erro["ultimo_erro"] = str(exc)
                item_erro["ultima_verificacao"] = agora_iso
                resultado_softwares.append(item_erro)
            else:
                resultado_softwares.append({
                    "id": fid,
                    "nome": fonte["nome"],
                    "fabricante": fonte["fabricante"],
                    "url": fonte["url"],
                    "versao_atual": None,
                    "versoes_candidatas": [],
                    "historico_versoes": [],
                    "hash_conteudo": None,
                    "nova_versao": False,
                    "data_ultima_atualizacao": None,
                    "ultima_verificacao": agora_iso,
                    "ultimo_erro": str(exc),
                })
            continue

        if versao_atual is None:
            ocorreram_falhas = True
            imprimir_diagnostico_sem_versao(texto)
            erro_msg = "Não foi possível detetar nenhuma versão válida na página."
            print(f"  [AVISO] {erro_msg}")
            if anterior:
                item_preservado = dict(anterior)
                item_preservado["ultimo_erro"] = erro_msg
                item_preservado["ultima_verificacao"] = agora_iso
                resultado_softwares.append(item_preservado)
            else:
                resultado_softwares.append({
                    "id": fid,
                    "nome": fonte["nome"],
                    "fabricante": fonte["fabricante"],
                    "url": fonte["url"],
                    "versao_atual": None,
                    "versoes_candidatas": candidatas,
                    "historico_versoes": [],
                    "hash_conteudo": hash_texto,
                    "nova_versao": False,
                    "data_ultima_atualizacao": None,
                    "ultima_verificacao": agora_iso,
                    "ultimo_erro": erro_msg,
                })
            continue

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
            "ultimo_erro": None,
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

    if ocorreram_falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
