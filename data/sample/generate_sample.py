"""Gera um dataset sintetico simulando saidas do LI-COR LI-7810SC + Smart Chamber
(CO2/CH4/H2O via OF-CEAS) e LI-7820 (N2O/H2O), em Rio Verde, GO.

Schema alinhado ao template real Rio_Verde_Geral_24-03-26.xlsx (46 colunas).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

FAZENDAS = ["IF-40", "ifgoiano", "Rio Verde", "Mata do Lobo", "Usina Decal"]
REGIOES = ["Sudoeste", "Centro", "Norte"]
CULTURAS = ["sorgo", "soja", "milho", "pastagem", "cana", "Mata"]
ESTACOES = ["Verão", "Outono", "Inverno", "Primavera"]
USOS = ["Lavoura", "Pastagem", "Mata"]
TEXTURAS = ["Argilosa", "Arenosa", "Media"]
MANEJOS = ["SPD", "Convencional", "ILP", "Nativo"]

n_pontos = 80
START = pd.Timestamp("2024-03-01")
HORIZON_DAYS = 90

linhas = []

for ponto in range(1, n_pontos + 1):
    fazenda = rng.choice(FAZENDAS)
    cultura = rng.choice(CULTURAS, p=[0.22, 0.22, 0.18, 0.13, 0.13, 0.12])
    regiao = rng.choice(REGIOES)
    textura = rng.choice(TEXTURAS)

    if cultura == "Mata":
        uso = "Mata"
        manejo = "Nativo"
    else:
        uso = rng.choice(["Lavoura", "Pastagem"])
        manejo = rng.choice(["SPD", "Convencional", "ILP"])

    lat = -17.78 + rng.normal(0, 0.05)
    lon = -50.93 + rng.normal(0, 0.05)
    if cultura == "Mata":
        lat -= 0.03
        lon += 0.02

    altitude = 720.0 + rng.normal(0, 25)

    day_offset = int(rng.integers(0, HORIZON_DAYS))
    base_ts = 26 + (1.5 if day_offset < 45 else -1.5) + rng.normal(0, 1.0)
    base_swc = 0.18 + (0.10 if day_offset > 45 else 0.0) + rng.normal(0, 0.04)
    base_swc = float(max(0.05, base_swc))

    if cultura == "Mata":
        base_ts -= 1.5
        base_swc += 0.04
        base_swc = float(min(0.45, base_swc))

    if day_offset < 22:
        estacao = "Verão"
    elif day_offset < 45:
        estacao = "Outono"
    elif day_offset < 67:
        estacao = "Inverno"
    else:
        estacao = "Primavera"

    for rep in (1, 2, 3):
        hour = int(rng.integers(8, 17))
        minute = int(rng.integers(0, 60))
        timestamp = START + pd.Timedelta(days=day_offset, hours=hour, minutes=minute)

        diel = 1.5 * np.sin((hour - 6) * np.pi / 12)
        ts = base_ts + diel + rng.normal(0, 0.4)
        swc = float(max(0.05, base_swc + rng.normal(0, 0.02)))

        ec = 0.20 + 0.5 * (swc - 0.2) + rng.normal(0, 0.04)
        h2o = 12 + 0.4 * (ts - 22) + rng.normal(0, 1.0)
        ta = ts + 1.5 + rng.normal(0, 0.8)
        doy = float(timestamp.dayofyear) + hour / 24.0

        co2_dry_init = 410 + rng.normal(0, 8)
        ch4_dry_init = 1.95 + rng.normal(0, 0.05)
        n2o_init = 0.335 + rng.normal(0, 0.005)
        co2_dry_mean = co2_dry_init + 1.2 * rep + rng.normal(0, 1.5)
        ch4_dry_mean = ch4_dry_init + 0.0008 * rep + rng.normal(0, 0.005)
        n2o_mean = n2o_init + 0.0003 * rep + rng.normal(0, 0.0008)

        # FCO2: T- and SWC-driven respiration
        fco2_base = 1.8 + 0.18 * (ts - 22) + 4.5 * (swc - 0.2)
        if cultura == "Mata":
            fco2_base *= 1.35
        fco2 = float(max(0.05, fco2_base + rng.normal(0, 0.6)))
        fco2_lin = fco2 + rng.normal(0, 0.1)

        fch4 = -0.012 + 0.0008 * (swc - 0.2) * 100 + rng.normal(0, 0.018)
        if cultura == "Mata":
            fch4 += rng.normal(0, 0.005)
        fch4_lin = fch4 + rng.normal(0, 0.003)

        # FN2O in mg N/m²/h (typical 0..0.05 with episodic spikes)
        fn2o_base = 0.0012 + 0.0006 * (swc - 0.2) * 10 + 0.00015 * (ts - 23)
        if cultura in ("soja", "milho") and estacao in ("Verão", "Primavera"):
            fn2o_base += float(rng.normal(0.008, 0.004))
        if cultura == "Mata":
            fn2o_base *= 0.6
        fn2o = float(max(0.0, fn2o_base + rng.normal(0, 0.0008)))
        fn2o_lin = fn2o + rng.normal(0, 0.0002)

        diag = 0 if rng.random() > 0.05 else int(rng.integers(1, 4))
        diag_init = 0 if rng.random() > 0.03 else 1

        r2_co2 = float(np.clip(0.92 + rng.normal(0, 0.05), 0.3, 0.999))
        r2_ch4 = float(np.clip(0.85 + rng.normal(0, 0.08), 0.2, 0.999))
        r2_n2o = float(np.clip(0.78 + rng.normal(0, 0.10), 0.2, 0.999))
        r2_co2_lin = float(np.clip(r2_co2 - 0.01, 0.2, 0.999))
        r2_ch4_lin = float(np.clip(r2_ch4 - 0.01, 0.2, 0.999))
        r2_n2o_lin = float(np.clip(r2_n2o - 0.01, 0.2, 0.999))

        cv_co2 = float(abs(rng.normal(0.12, 0.05)))
        cv_ch4 = float(abs(rng.normal(0.18, 0.08)))
        cv_n2o = float(abs(rng.normal(0.22, 0.10)))
        cv_co2_lin = float(abs(rng.normal(0.13, 0.05)))
        cv_ch4_lin = float(abs(rng.normal(0.20, 0.08)))
        cv_n2o_lin = float(abs(rng.normal(0.24, 0.10)))

        linhas.append({
            "ID": f"P{ponto:03d}",
            "LATITUDE": round(lat, 6),
            "LONGITUDE": round(lon, 6),
            "Fazenda": fazenda,
            "Região": regiao,
            "Textura": textura,
            "Uso atual": uso,
            "Cultura": cultura,
            "Manejo": manejo,
            "Estação": estacao,
            "DATE_TIME initial_value": timestamp,
            "DIAGNOSTIC initial_value": diag_init,
            "ALTITUDE initial_value": round(altitude, 2),
            "LABEL": f"P{ponto:03d}_R{rep}",
            "REP": rep,
            "CH4_DRY initial_value": round(ch4_dry_init, 4),
            "CO2_DRY initial_value": round(co2_dry_init, 4),
            "CH4_DRY mean": round(ch4_dry_mean, 4),
            "CO2_DRY mean": round(co2_dry_mean, 4),
            "EC_2 initial_value": round(float(ec), 4),
            "SWC_2 initial_value": round(swc, 4),
            "FCH4_DRY": round(fch4, 6),
            "FCH4_DRY R2": round(r2_ch4, 4),
            "H2O initial_value": round(float(h2o), 4),
            "TS_2 initial_value": round(ts, 3),
            "FCH4_DRY CV": round(cv_ch4, 4),
            "FCH4_DRY LIN": round(fch4_lin, 6),
            "FCH4_DRY LIN_R2": round(r2_ch4_lin, 4),
            "FCO2_DRY": round(fco2, 4),
            "FCO2_DRY R2": round(r2_co2, 4),
            "FCO2_DRY LIN": round(fco2_lin, 4),
            "FCO2_DRY LIN_R2": round(r2_co2_lin, 4),
            "FCH4_DRY LIN_CV": round(cv_ch4_lin, 4),
            "FCO2_DRY CV": round(cv_co2, 4),
            "FCO2_DRY LIN_CV": round(cv_co2_lin, 4),
            "DOY initial_value": round(doy, 3),
            "TA initial_value": round(float(ta), 3),
            "DIAG initial_value": diag,
            "N2O initial_value": round(n2o_init, 6),
            "N2O mean": round(n2o_mean, 6),
            "FN2O": round(fn2o, 6),
            "FN2O R2": round(r2_n2o, 4),
            "FN2O CV": round(cv_n2o, 4),
            "FN2O LIN": round(fn2o_lin, 6),
            "FN2O LIN_R2": round(r2_n2o_lin, 4),
            "FN2O LIN_CV": round(cv_n2o_lin, 4),
        })

df = pd.DataFrame(linhas).sort_values("DATE_TIME initial_value").reset_index(drop=True)
df.to_excel("Dados_Fluxo_Solo_SAMPLE.xlsx", sheet_name="Fluxo", index=False)
df.to_csv("Dados_Fluxo_Solo_SAMPLE.csv", index=False, encoding="utf-8-sig")
print(f"Gerado: {len(df)} linhas, {len(df.columns)} colunas")
print(f"Culturas: {sorted(df['Cultura'].unique())}")
print(f"Estações: {sorted(df['Estação'].unique())}")
print(f"Período: {df['DATE_TIME initial_value'].min()} -> {df['DATE_TIME initial_value'].max()}")
