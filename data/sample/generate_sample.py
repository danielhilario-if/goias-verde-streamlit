"""Gera um dataset sintetico simulando saidas do LI-COR LI-7810SC + Smart Chamber.

O LI-7810 e um analisador de gases traco a laser (OF-CEAS), nao um IRGA
tradicional. Este script reproduz o esquema de colunas esperado pelo app
goias-verde-streamlit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

FAZENDAS = ["Fazenda_RV01", "Fazenda_RV02", "Fazenda_RV03", "Fazenda_RV04"]
CULTURAS = ["Soja", "Milho", "Pastagem", "Cana"]
EPOCAS = ["Seca", "Aguas"]
USOS = ["Lavoura", "Pastagem", "Mata"]
TEXTURAS = ["Argilosa", "Arenosa", "Media"]
MANEJOS = ["SPD", "Convencional", "ILP"]

n_pontos = 80
linhas = []

for ponto in range(1, n_pontos + 1):
    fazenda = rng.choice(FAZENDAS)
    cultura = rng.choice(CULTURAS)
    epoca = rng.choice(EPOCAS)
    uso = rng.choice(USOS)
    textura = rng.choice(TEXTURAS)
    manejo = rng.choice(MANEJOS)

    lat = -17.78 + rng.normal(0, 0.05)
    lon = -50.93 + rng.normal(0, 0.05)

    ts_base = 26 if epoca == "Seca" else 23
    swc_base = 0.18 if epoca == "Seca" else 0.32

    for rep in (1, 2, 3):
        ts = ts_base + rng.normal(0, 1.2)
        swc = max(0.05, swc_base + rng.normal(0, 0.04))

        fco2 = max(0.1, 1.8 + 0.18 * (ts - 22) + 4.5 * (swc - 0.2) + rng.normal(0, 0.6))
        fch4 = -0.012 + 0.0008 * (swc - 0.2) * 100 + rng.normal(0, 0.018)

        diag = 0 if rng.random() > 0.05 else int(rng.integers(1, 4))
        r2_co2 = float(np.clip(0.92 + rng.normal(0, 0.05), 0.3, 0.999))
        r2_ch4 = float(np.clip(0.85 + rng.normal(0, 0.08), 0.2, 0.999))

        linhas.append(
            {
                "ID": f"P{ponto:03d}",
                "Fazenda": fazenda,
                "Cultura": cultura,
                "Época": epoca,
                "Uso atual": uso,
                "Textura": textura,
                "Manejo": manejo,
                "Latitude": round(lat, 6),
                "Longitude": round(lon, 6),
                "Data": pd.Timestamp("2024-03-01") + pd.Timedelta(days=int(rng.integers(0, 60))),
                "REP": rep,
                "Diagnostic Initial_value": diag,
                "TS_2 initial_value": round(ts, 3),
                "SWC_2 initial_value": round(swc, 4),
                "FCO2_DRY": round(fco2, 4),
                "FCH4_DRY": round(fch4, 6),
                "FCO2_DRY R2": round(r2_co2, 4),
                "FCH4_DRY LIN_R2": round(r2_ch4, 4),
                "FCO2_DRY LIN_R2": round(r2_co2 - 0.01, 4),
                "FCH4_DRY R2": round(r2_ch4 - 0.01, 4),
                "CO2_DRY REPLICATE": rep,
                "CH4_DRY REPLICATE": rep,
                "REPLICATE": rep,
                "LABEL": f"P{ponto:03d}_R{rep}",
            }
        )

df = pd.DataFrame(linhas)
df.to_excel("Dados_Fluxo_Solo_SAMPLE.xlsx", sheet_name="Fluxo", index=False)
df.to_csv("Dados_Fluxo_Solo_SAMPLE.csv", index=False, encoding="utf-8-sig")
print(f"Gerado: {len(df)} linhas, {len(df.columns)} colunas")
