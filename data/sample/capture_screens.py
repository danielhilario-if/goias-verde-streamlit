"""Captura screenshots das paginas do app Streamlit chamberflux.

Usa Playwright para abrir cada pagina, fazer upload do dataset de exemplo,
aplicar interacoes basicas e salvar as capturas em texto/figs/screenshots/.
A linguagem da UI e definida pela constante LANG (pt/en/es).
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "texto" / "SoftwareAndImpacts_IRGA" / "figs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_FILE = Path(__file__).parent / "Dados_Fluxo_Solo_SAMPLE.xlsx"

URL = "http://localhost:8501"
MAX_DIM = 1600
LANG = "en"

# Default language displayed in the sidebar dropdown when the app first loads.
# Must match DEFAULT_LANGUAGE in src/i18n/translations.py.
DEFAULT_LANG_DISPLAY = "Portugues"

# Display name of the target language inside the sidebar selectbox.
LANG_DISPLAY = {"pt": "Portugues", "en": "English", "es": "Espanol"}

LABELS = {
    "pt": {
        "load_dataset": "Carregar Dataset",
        "apply_pipeline": "Aplicar pipeline",
        "nav_pipeline": "Pipeline e Processamento",
        "nav_eda": "EDA",
        "nav_regression": "Regressao",
        "nav_modeling": "Modelagem",
        "nav_spatial": "Analise Espacial",
        "nav_timeseries": "Serie Temporal",
        "nav_comparative": "Comparacao por grupo",
        "tab_quality": "Qualidade dos Dados",
        "tab_bivariate": "Relacoes Bivariadas",
        "tab_boxplots": "Boxplots por Grupo",
        "tab_scatter": "Dispersao",
        "tab_correlation": "Correlacao",
        "tab_eda_spatial": "Espacial",
    },
    "en": {
        "load_dataset": "Load dataset",
        "apply_pipeline": "Apply pipeline",
        "nav_pipeline": "Pipeline & Processing",
        "nav_eda": "EDA",
        "nav_regression": "Regression",
        "nav_modeling": "Modeling",
        "nav_spatial": "Spatial Analysis",
        "nav_timeseries": "Time Series",
        "nav_comparative": "Group comparison",
        "tab_quality": "Data Quality",
        "tab_bivariate": "Bivariate Relations",
        "tab_boxplots": "Boxplots by Group",
        "tab_scatter": "Scatter",
        "tab_correlation": "Correlation",
        "tab_eda_spatial": "Spatial",
    },
    "es": {
        "load_dataset": "Cargar Dataset",
        "apply_pipeline": "Aplicar pipeline",
        "nav_pipeline": "Pipeline y Procesamiento",
        "nav_eda": "EDA",
        "nav_regression": "Regresion",
        "nav_modeling": "Modelado",
        "nav_spatial": "Analisis Espacial",
        "nav_timeseries": "Serie Temporal",
        "nav_comparative": "Comparacion por grupo",
        "tab_quality": "Calidad de los Datos",
        "tab_bivariate": "Relaciones Bivariadas",
        "tab_boxplots": "Boxplots por Grupo",
        "tab_scatter": "Dispersion",
        "tab_correlation": "Correlacion",
        "tab_eda_spatial": "Espacial",
    },
}


def shoot(page, name: str, *, full=False):
    out = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(out), full_page=full)
    img = Image.open(out)
    img.thumbnail((MAX_DIM, MAX_DIM))
    img.save(out, optimize=True)
    print(f"saved {out.name} ({img.size[0]}x{img.size[1]})")


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


def switch_language(page, target_lang: str) -> None:
    """Clica no selectbox 'Idioma' (lang default = pt) e seleciona o alvo."""
    if target_lang == "pt":
        return
    target_display = LANG_DISPLAY[target_lang]
    # Streamlit selectbox renderiza um listbox aria-haspopup. Selecionar pelo
    # valor atual exibido (DEFAULT_LANG_DISPLAY) e clicar abre o dropdown.
    try:
        combo = page.locator(f'div[data-baseweb="select"]:has-text("{DEFAULT_LANG_DISPLAY}")').first
        combo.click()
        time.sleep(0.7)
        page.locator(f'li[role="option"]:has-text("{target_display}")').first.click()
        time.sleep(2.0)
    except Exception as exc:
        print(f"language switch failed (continuing in default): {exc}")


def main():
    L = LABELS[LANG]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        time.sleep(3.0)

        switch_language(page, LANG)

        # 1. Tela inicial / Upload
        shoot(page, "01_upload_inicial")

        # 2. Faz upload do arquivo
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(SAMPLE_FILE))
        time.sleep(2.5)
        try:
            page.get_by_role("button", name=L["load_dataset"]).click()
        except Exception:
            pass
        time.sleep(3.5)
        shoot(page, "02_upload_carregado")

        # 3. Pipeline e Processamento
        click_nav(page, L["nav_pipeline"])
        time.sleep(2.0)
        shoot(page, "03_pipeline_form")
        try:
            page.get_by_role("button", name=L["apply_pipeline"]).click()
            time.sleep(4.0)
            shoot(page, "04_pipeline_aplicado")
        except Exception as exc:
            print(f"pipeline apply failed: {exc}")

        # 4. EDA
        click_nav(page, L["nav_eda"])
        time.sleep(3.0)
        shoot(page, "05_eda_resumo")
        for label, name in (
            (L["tab_quality"], "06_eda_qualidade"),
            (L["tab_bivariate"], "07_eda_distribuicoes"),
            (L["tab_boxplots"], "08_eda_boxplots"),
            (L["tab_scatter"], "09_eda_dispersao"),
            (L["tab_correlation"], "10_eda_correlacao"),
            (L["tab_eda_spatial"], "11_eda_espacial"),
        ):
            try:
                page.get_by_role("tab", name=label).click()
                time.sleep(3.0)
                shoot(page, name)
            except Exception as exc:
                print(f"tab '{label}' failed: {exc}")

        # 5. Regressao
        click_nav(page, L["nav_regression"])
        time.sleep(4.0)
        shoot(page, "12_regressao")

        # 6. Modelagem
        click_nav(page, L["nav_modeling"])
        time.sleep(8.0)
        shoot(page, "13_modelagem")

        # 7. Spatial
        try:
            click_nav(page, L["nav_spatial"])
            time.sleep(4.0)
            shoot(page, "14_spatial")
        except Exception as exc:
            print(f"spatial nav failed: {exc}")

        # 8. Time Series
        try:
            click_nav(page, L["nav_timeseries"])
            time.sleep(4.0)
            shoot(page, "15_timeseries")
        except Exception as exc:
            print(f"timeseries nav failed: {exc}")

        # 9. Comparativo
        try:
            click_nav(page, L["nav_comparative"])
            time.sleep(3.0)
            shoot(page, "16_comparative")
        except Exception as exc:
            print(f"comparative nav failed: {exc}")

        browser.close()


if __name__ == "__main__":
    main()
