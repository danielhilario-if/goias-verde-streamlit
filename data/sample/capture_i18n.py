"""Captura screenshots do app em pt, en e es para validar a tradução.

Para cada idioma, faz upload do dataset, aplica o pipeline e captura
4 telas-chave: Upload (carregado), Pipeline (aplicado), EDA Resumo e Modelagem.
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "texto" / "SoftwareAndImpacts_IRGA" / "figs" / "screenshots_i18n"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_FILE = Path(__file__).parent / "Dados_Fluxo_Solo_SAMPLE.xlsx"

URL = "http://localhost:8765"

LANGS = [
    ("pt", "Portugues"),
    ("en", "English"),
    ("es", "Espanol"),
]

NAV_BY_LANG = {
    "pt": {"pipeline": "Pipeline e Processamento", "eda": "EDA", "modeling": "Modelagem"},
    "en": {"pipeline": "Pipeline & Processing", "eda": "EDA", "modeling": "Modeling"},
    "es": {"pipeline": "Pipeline y Procesamiento", "eda": "EDA", "modeling": "Modelado"},
}

LOAD_BTN_BY_LANG = {
    "pt": "Carregar Dataset",
    "en": "Load dataset",
    "es": "Cargar dataset",
}

APPLY_BTN_BY_LANG = {
    "pt": "Aplicar pipeline",
    "en": "Apply pipeline",
    "es": "Aplicar pipeline",
}


def shoot(page, name: str):
    out = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(out), full_page=True)
    print(f"saved {out.name}")


def click_nav(page, label: str):
    for frame in page.frames:
        try:
            link = frame.locator("a.nav-link", has_text=label).first
            if link.count() > 0:
                link.click()
                time.sleep(2.5)
                return
        except Exception:
            continue
    raise RuntimeError(f"nav '{label}' not found")


def select_language(page, lang_label: str):
    selector = page.locator('[data-testid="stSelectbox"]').first
    selector.click()
    time.sleep(0.5)
    page.get_by_text(lang_label, exact=True).first.click()
    time.sleep(2.0)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        time.sleep(3.0)

        for code, label in LANGS:
            if code != "pt":  # pt e o default
                select_language(page, label)

            page.locator('input[type="file"]').set_input_files(str(SAMPLE_FILE))
            time.sleep(2.0)
            try:
                page.get_by_role("button", name=LOAD_BTN_BY_LANG[code]).click()
                time.sleep(3.0)
            except Exception:
                pass
            shoot(page, f"01_upload_{code}")

            click_nav(page, NAV_BY_LANG[code]["pipeline"])
            try:
                page.get_by_role("button", name=APPLY_BTN_BY_LANG[code]).click()
                time.sleep(4.0)
            except Exception:
                pass
            shoot(page, f"02_pipeline_{code}")

            click_nav(page, NAV_BY_LANG[code]["eda"])
            time.sleep(3.0)
            shoot(page, f"03_eda_{code}")

            click_nav(page, NAV_BY_LANG[code]["modeling"])
            time.sleep(8.0)
            shoot(page, f"04_modeling_{code}")

            # volta pro Upload pra resetar estado quando trocar idioma
            page.goto(URL, wait_until="networkidle")
            time.sleep(2.5)

        browser.close()


if __name__ == "__main__":
    main()
