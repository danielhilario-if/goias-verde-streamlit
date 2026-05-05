# Goiás Verde Streamlit

> An open-source web application for exploratory data analysis and machine
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

`goias-verde-streamlit` consolidates the entire chamber-based GHG flux
analysis workflow into a single web application: ingestion of CSV/XLSX
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

1. **Upload** — CSV/XLSX upload with sheet selection and in-memory cache.
2. **Pipeline** — Five configurable filters with a transparent step-by-step
   report: variable removal, diagnostic-flag filter, R² threshold,
   per-group quantile outliers, replicate aggregation (mean/median).
3. **EDA** — Nine tabs: statistical summary, data quality, univariate
   distributions, boxplots/violins, scatter matrix, correlation heatmap,
   spatial map, **time-series of fluxes**, **categorical composition**.
4. **Regression** — Bivariate regression presets including the **Q₁₀
   thermal sensitivity** preset (van't Hoff equation) commonly reported
   in the soil-flux literature, plus a fully customizable regression
   block with hue and facet support.
5. **Modeling** — Supervised regression with five estimators (Linear,
   Random Forest, Gradient Boosting, Decision Tree, KNN), holdout +
   cross-validation, **predicted vs. observed plot** and feature
   importance bar chart.
6. **Authentication** — Optional Supabase login layer for institutional
   deployments.
7. **i18n** — Built-in selector for **Portuguese / English / Spanish**.

## Project layout

```
goias-verde-streamlit/
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

- Python 3.10
- Dependencies listed in [`requirements.txt`](./requirements.txt) (Streamlit,
  scikit-learn, pandas, NumPy, Matplotlib, seaborn, Supabase).

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
@article{Souza2025GoiasVerde,
  author  = {da Silva Souza, Leandro Rodrigues and Jakelaitis, Adriano and
             Alves da Silva, Daiane and Tonus Ribeiro, Caio and
             Hil{\'a}rio da Silva, Daniel and Alves Pereira, Adriano and
             de Oliveira Andrade, Adriano},
  title   = {{Goi{\'a}s Verde Streamlit}: An open-source web application
             for exploratory analysis and machine learning of soil
             greenhouse gas fluxes measured with portable laser-based
             trace gas analyzers},
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
