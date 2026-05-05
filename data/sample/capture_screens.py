"""Captura screenshots das paginas do app Streamlit goias-verde-streamlit.

Usa Playwright para abrir cada pagina, fazer upload do dataset de exemplo,
aplicar interacoes basicas e salvar as capturas em texto/figs/screenshots/.
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "texto" / "SoftwareAndImpacts_IRGA" / "figs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_FILE = Path(__file__).parent / "Dados_Fluxo_Solo_SAMPLE.xlsx"

URL = "http://localhost:8765"


def shoot(page, name: str, *, full=True):
    out = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(out), full_page=full)
    print(f"saved {out.name}")


def click_nav(page, label: str):
    # streamlit-option-menu eh um custom component renderizado dentro de iframe.
    for frame in page.frames:
        try:
            link = frame.locator('a.nav-link', has_text=label).first
            if link.count() > 0:
                link.click()
                time.sleep(2.5)
                return
        except Exception:
            continue
    raise RuntimeError(f"nav link '{label}' nao encontrado em nenhum frame")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        time.sleep(3.0)

        # 1. Tela inicial / Upload
        shoot(page, "01_upload_inicial")

        # 2. Faz upload do arquivo
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(SAMPLE_FILE))
        time.sleep(2.5)
        # Selecionar a sheet (caso aparece)
        try:
            page.get_by_role("button", name="Carregar Dataset").click()
        except Exception:
            pass
        time.sleep(3.5)
        shoot(page, "02_upload_carregado")

        # 3. Pipeline e Processamento
        click_nav(page, "Pipeline e Processamento")
        time.sleep(2.0)
        shoot(page, "03_pipeline_form")
        try:
            page.get_by_role("button", name="Aplicar pipeline").click()
            time.sleep(4.0)
            shoot(page, "04_pipeline_aplicado")
        except Exception as exc:
            print(f"pipeline apply failed: {exc}")

        # 4. EDA
        click_nav(page, "EDA")
        time.sleep(3.0)
        shoot(page, "05_eda_resumo")
        # Aba Qualidade
        try:
            page.get_by_role("tab", name="Qualidade dos Dados").click()
            time.sleep(2.0)
            shoot(page, "06_eda_qualidade")
        except Exception:
            pass
        # Aba Relacoes Bivariadas
        try:
            page.get_by_role("tab", name="Relações Bivariadas").click()
            time.sleep(3.0)
            shoot(page, "07_eda_distribuicoes")
        except Exception:
            pass
        # Aba Boxplots
        try:
            page.get_by_role("tab", name="Boxplots por Grupo").click()
            time.sleep(3.0)
            shoot(page, "08_eda_boxplots")
        except Exception:
            pass
        # Aba Dispersao
        try:
            page.get_by_role("tab", name="Dispersão").click()
            time.sleep(4.0)
            shoot(page, "09_eda_dispersao")
        except Exception:
            pass
        # Aba Correlacao
        try:
            page.get_by_role("tab", name="Correlação").click()
            time.sleep(3.0)
            shoot(page, "10_eda_correlacao")
        except Exception:
            pass
        # Aba Espacial
        try:
            page.get_by_role("tab", name="Espacial").click()
            time.sleep(3.0)
            shoot(page, "11_eda_espacial")
        except Exception:
            pass

        # 5. Regressao
        click_nav(page, "Regressão")
        time.sleep(4.0)
        shoot(page, "12_regressao")

        # 6. Modelagem
        click_nav(page, "Modelagem")
        time.sleep(8.0)  # treinamento leva alguns segundos
        shoot(page, "13_modelagem")

        browser.close()


if __name__ == "__main__":
    main()
