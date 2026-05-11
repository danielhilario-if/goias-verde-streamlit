# ChamberFlux

> An open-source interactive analysis platform for exploratory data analysis and machine
> learning of soil greenhouse gas (GHG) fluxes measured with portable
> laser-based trace gas analyzers using OF-CEAS spectroscopy
> (LI-COR LI-7810SC for CH₄/CO₂/H₂O + Smart Chamber 8200-01S, and LI-7820
> for N₂O/H₂O).

[English](./README.md) | [Português](./README.pt.md) | [Español](./README.es.md)

**Version:** 1.0  
**Authors:** Souza, L. R. da S. et al.  
**License:** GPLv2 with mandatory citation clause — see [LICENSE](./LICENSE).

---

## Overview

`chamberflux` consolidates the entire chamber-based GHG flux
analysis workflow into a single interactive analysis platform: ingestion of CSV/XLSX
exports produced by laser-based trace gas analyzers (such as the LI-COR
LI-78xx series, which use OF-CEAS spectroscopy rather than the
infrared-absorption technique of traditional IRGAs), a configurable
data-cleaning pipeline, exploratory analyses, bivariate regression and
supervised machine-learning regression. The application is part of the
**Goiás Verde** initiative at *Instituto Federal Goiano – Campus Rio Verde*
and the *Center of Excellence in Exponential Agriculture (CEAGRE)*. It is
written in Python with [Streamlit](https://streamlit.io) and is dataset
agnostic — any tabular dataset that fits the schema of a chamber GHG flux
campaign can be analysed.

## Features

1. **Upload** — CSV/XLSX upload with sheet selection, in-memory cache, and an
   **explicit schema validation** that classifies expected columns as
   *required*, *recommended* or *optional*, checks types, flags sentinel
   values such as -9999, and verifies that latitude/longitude are within
   plausible ranges. Missing columns never block the upload — they simply
   disable the dependent features.
2. **Pipeline** — Seven configurable filters with a transparent step-by-step
   report: variable removal, diagnostic-flag filter, R² threshold,
   **user-defined CV/quality threshold filter** (use `≤` on the coefficient
   of variation when fluxes approach zero and R² is no longer informative;
   accepts any numeric column with either `≥` or `≤`), per-group quantile
   outliers, **robust seasonal Q10–Q90 cleaning** (per gas, per season,
   with a tunable fence factor), and replicate aggregation (mean/median).
3. **EDA** — Twelve tabs: statistical summary, data quality, univariate
   distributions, boxplots/violins, scatter matrix, **correlation heatmap
   (Pearson / Spearman / Kendall)**, spatial map, time-series of fluxes,
   categorical composition, **inference (Kruskal-Wallis + normality
   tests Shapiro-Wilk / Anderson-Darling / D'Agostino-Pearson + VIF
   multicollinearity)**, **hotspot rankings** and a **multi-method
   outlier audit** (Z-score, IQR, Isolation Forest, LOF, Elliptic
   Envelope plus a consensus criterion).
4. **Regression** — Bivariate regression presets including the **Q₁₀
   thermal sensitivity** preset (van't Hoff equation) commonly reported
   in the soil-flux literature, plus a fully customizable regression
   block with hue and facet support.
5. **Modeling** — Supervised regression with five estimators (Linear,
   Random Forest, Gradient Boosting, Decision Tree, KNN), holdout +
   cross-validation, predicted vs. observed plot and feature importance
   bar chart.
6. **Spatial Analysis** — Six tabs: **IDW interpolation** (configurable
   grid and power exponent, optional faceting), **Moran's I global +
   LISA local clustering** (HH/LL/HL/LH/NS), **Getis-Ord G\*** hotspot
   detection, **regular UTM grid aggregation** (1 km cells by default),
   **ordinary kriging** with a fitted spherical variogram, and a **Rio
   Verde basemap** layer fetched via `geobr` for institutional context.
7. **Time Series** — Daily aggregation (mean/median) and **STL
   decomposition** (trend + seasonal + residual) with configurable
   seasonal period and trend/seasonal-strength metrics.
8. **Group comparison** — Configurable two-group page (preset
   *Forest × Other* available for the Mata-vs-Cropland question, but the
   page accepts any partition of any categorical column): mean ± SE and
   median per group, **Mann-Whitney U test**, **user-selected log-linear
   regression** $\log(Y) \sim X$ per group, and an **hourly cumulative
   flux profile**.
9. **Authentication** — Optional Supabase login layer for institutional
   deployments.
10. **i18n** — Built-in selector for **Portuguese / English / Spanish**.

## Project layout

```
chamberflux/
├── app.py                     # Streamlit entry point
├── src/
│   ├── auth.py                # Supabase authentication
│   ├── components/            # Sidebar, dataset toggle
│   ├── config/                # Settings, constants, defaults
│   ├── i18n/                  # Translation module
│   │   ├── __init__.py
│   │   ├── translations.py
│   │   └── locales/           # JSON files (pt, en, es)
│   ├── ml/                    # Model registry
│   ├── pages/                 # Five UI pages
│   ├── pipeline.py            # Pure-function cleaning primitives
│   └── state.py               # Streamlit session-state helpers
├── docs/                      # Architecture, deployment, contributing, i18n
├── tests/                     # pytest suite
├── data/sample/               # Synthetic IRGA-style dataset
├── scripts/                   # i18n_audit and other maintenance scripts
├── assets/                    # CEAGRE logo
├── requirements.txt
├── LICENSE
├── CITATION.cff
└── citation.bib
```

## Requirements

- Python 3.10+
- Dependencies listed in [`requirements.txt`](./requirements.txt):
  - **Core**: Streamlit, pandas, NumPy, Matplotlib, seaborn, scikit-learn,
    openpyxl, Supabase.
  - **Statistics**: scipy, statsmodels (STL, VIF, normality tests).
  - **Geospatial**: geopandas, shapely, geobr (Brazilian municipal
    boundaries), libpysal (KNN spatial weights), esda (Moran's I, LISA,
    Getis-Ord G\*).

> On Windows, modern pip wheels (`shapely>=2`, `pyproj`, `pyogrio`,
> `geopandas>=1`) are self-contained — no system GDAL needed. The Conda
> fallback (`conda install -c conda-forge geopandas libpysal esda`) is
> only required on platforms without prebuilt wheels; see
> [`docs/deployment.md`](./docs/deployment.md) for full instructions.

## Installation

```bash
python3.10 -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -U pip wheel
pip install -r requirements.txt
```

If you also want to regenerate the manuscript figures with the
Playwright-based capture scripts under `data/sample/`, install the
optional development dependencies as well:

```bash
pip install -r requirements-dev.txt
playwright install chromium
```

## Running

```bash
python -m streamlit run app.py
```

> Always use `python -m streamlit` to guarantee the `.venv` Streamlit is used.

## Running the tests

```bash
pytest tests/ -v
```

## Sample dataset

A synthetic dataset (240 rows × 24 columns) replicating the schema of the
LI-COR LI-7810SC + Smart Chamber export is provided under
[`data/sample/`](./data/sample/) for evaluation. Generate it from scratch with:

```bash
cd data/sample
python generate_sample.py
```

## Internationalisation

Add a new language by creating `src/i18n/locales/<code>.json` with the same
keys as `pt.json`, registering the code in
`src/i18n/translations.py::AVAILABLE_LANGUAGES`, and validating with:

```bash
python -m scripts.i18n_audit
```

See [`docs/i18n.md`](./docs/i18n.md) for the full guide.

## Supabase authentication (optional)

To enable login:

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Fill `url` and `publishable_key` for your Supabase project.
3. Restart the app.

See [`docs/deployment.md`](./docs/deployment.md) for the full deployment guide.

## License

This project is licensed under the **GNU General Public License version 2**
or later, **with a mandatory citation clause**. Any academic or commercial
use of the software must cite the publication referenced below. See the
[LICENSE](./LICENSE) file for the full text.

## Citation

If you use this software in your research, **you must cite the following
publication**:

```bibtex
@article{Souza2026ChamberFlux,
  author  = {Souza, Leandro Rodrigues da Silva and
             Hil{\'a}rio da Silva, Daniel and Abade, Andr{\'e} and Thomazini, Andr{\'e} and
             Cabral Filho, Fernando Rodrigues and Paim, Tiago do Prado and
             Pinto dos Santos, Erli and Cordeiro, Douglas Farias and
             Alves da Silva, Daiane and Costa, Alan Carlos da},
  title   = {{ChamberFlux}: An open-source interactive analysis platform
             for exploratory analysis and machine learning of soil
             greenhouse gas fluxes measured with the {LI-COR} {LI-7810SC}
             (CH$_4$/CO$_2$/H$_2$O) and {LI-7820} (N$_2$O/H$_2$O) portable
             laser-based trace gas analyzers},
  journal = {Software Impacts},
  year    = {2025},
  doi     = {10.1016/j.simpa.2025.XXXXXX}
}
```

GitHub also provides a "Cite this repository" button via [`CITATION.cff`](./CITATION.cff).

## Support

For issues or questions, open a GitHub issue or contact
**leandrorodrigues.s@gmail.com**.

## Acknowledgements

This work was supported by CNPq, CAPES, FAPEMIG, FAPEG, the Federal
Institute of Education, Science, and Technology Goiano (IF Goiano –
Campus Rio Verde and Campus Cristalina), and the Center of Excellence
in Exponential Agriculture (CEAGRE).
