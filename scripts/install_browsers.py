"""
Instala o browser Chromium do Playwright no container.
Execute após instalar as dependências Python:
    python scripts/install_browsers.py
"""
import subprocess
import sys


def install_chromium() -> None:
    print("Instalando Playwright Chromium...")
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Erro ao instalar Chromium.")
        sys.exit(1)
    print("Chromium instalado com sucesso.")


if __name__ == "__main__":
    install_chromium()
