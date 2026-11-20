import re
import subprocess
import sys
from pathlib import Path

# Aceita nomes como verificar_versoes_v1.1.py ou qualquer_coisa_v1.2.3.py
PADRAO_VERSAO = re.compile(r"_v(\d+(?:\.\d+)+)\.py$", re.IGNORECASE)


def chave_versao(caminho: Path) -> tuple[int, ...]:
    match = PADRAO_VERSAO.search(caminho.name)
    if not match:
        return ()
    return tuple(int(parte) for parte in match.group(1).split("."))


def encontrar_script_mais_recente(pasta: Path = Path(".")) -> Path | None:
    candidatos = [
        p for p in pasta.glob("*_v*.py")
        if p.is_file() and PADRAO_VERSAO.search(p.name)
    ]
    if not candidatos:
        return None
    return max(candidatos, key=chave_versao)


def main() -> None:
    script_escolhido = encontrar_script_mais_recente(Path("."))

    # Caso ainda só exista o nome antigo sem sufixo _vX.Y
    if script_escolhido is None and Path("verificar_versoes.py").exists():
        script_escolhido = Path("verificar_versoes.py")

    if script_escolhido is None:
        print("Erro: não foi encontrado nenhum script de verificação.", file=sys.stderr)
        sys.exit(1)

    print(f"A executar a versão mais recente detetada: {script_escolhido.name}")
    resultado = subprocess.run([sys.executable, str(script_escolhido)], check=False)
    sys.exit(resultado.returncode)


if __name__ == "__main__":
    main()