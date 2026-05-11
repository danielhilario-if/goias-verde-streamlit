# Architecture

`chamberflux` is a single-page Streamlit application backed by a
small Python package under `src/`. The runtime is a single process; data is
held in `st.session_state` and cached with `@st.cache_data` to avoid re-parsing
files between page navigations.

## Module layout

```
src/
├── auth.py                # Optional Supabase login layer
├── components/            # Reusable UI components
│   ├── dataset_controls.py
│   └── sidebar.py
├── config/
│   └── settings.py        # NavigationItem, primary color, default columns
├── i18n/
│   ├── translations.py    # Loader + AVAILABLE_LANGUAGES dict
│   └── locales/{pt,en,es}.json
├── ml/
│   └── model_registry.py  # Wraps scikit-learn estimators in a registry
├── pages/                 # One module per left-menu entry
│   ├── upload.py
│   ├── pipeline.py
│   ├── eda.py
│   ├── regression.py
│   ├── modeling.py
│   ├── spatial.py
│   ├── timeseries.py
│   └── comparative.py
├── pipeline.py            # Pure-function cleaning primitives
├── schema.py              # Upload-time schema validation
└── state.py               # Session-state helpers
```

The entry point `app.py` reads the navigation selection from
`src/config/settings.py::NAVIGATION_ITEMS`, routes the request to a
`render()` function in the matching `src/pages/` module, and delegates
authentication to `src.auth` when enabled.

## Page responsibilities

| Page              | Module                         | Purpose                                                                       |
| ----------------- | ------------------------------ | ----------------------------------------------------------------------------- |
| Upload            | `pages/upload.py`              | File ingestion, schema validation, in-memory caching                          |
| Pipeline          | `pages/pipeline.py`            | Configurable cleaning steps (drop, diagnostic, R², CV/threshold, outliers, Q10–Q90, REP) |
| EDA               | `pages/eda.py`                 | 12 tabs: descriptives, quality, distributions, boxplots, scatter, correlation, spatial, temporal, composition, inference, hotspots, outliers |
| Regression        | `pages/regression.py`          | Bivariate presets + free regression                                           |
| Modeling          | `pages/modeling.py`            | Holdout + CV comparison of five sklearn estimators                            |
| Spatial Analysis  | `pages/spatial.py`             | IDW, Moran's I/LISA, Getis-Ord G\*, UTM grid, ordinary kriging, geobr basemap |
| Time Series       | `pages/timeseries.py`          | Daily aggregation + STL decomposition                                         |
| Group comparison  | `pages/comparative.py`         | Two-group summary, log-linear regression, hourly cumulative profile           |

## Data flow

```
                 ┌──────────────┐
   user upload → │ Upload page  │ → set_loaded_dataset()
                 └──────┬───────┘
                        │ session_state["df_raw"]
                        ▼
                 ┌──────────────┐
                 │ Pipeline page│ → set_processed_dataset()
                 └──────┬───────┘
                        │ session_state["df_processed"]
                        ▼
   any of: EDA, Regression, Modeling, Spatial, Time Series, Comparative
```

Pages always read from `session_state` via `state.get_active_dataframe(...)`,
toggling between *raw* and *processed* using the dataset toggle defined in
`components/dataset_controls.py`.

## Cleaning primitives (`src/pipeline.py`)

Each filter is a pure function returning `(DataFrame, StepLog)`. Pipeline UI
calls them in sequence and concatenates the logs with `build_step_report` for
the transparent step-by-step report.

| Function                   | Step                                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `remove_columns`           | Drop manufacturer-redundant columns                                                                                                                   |
| `apply_diagnostic_filter`  | Keep `Diagnostic == 0`                                                                                                                                |
| `apply_r2_threshold`       | Drop rows with low linear-fit R² for CO₂/CH₄                                                                                                          |
| `apply_threshold_filter`   | Generic `≥`/`≤` filter on any numeric quality column (e.g. **CV of CO₂/CH₄/N₂O**); recommended over R² when fluxes are near zero (R² collapses, CV stays informative) |
| `filter_outliers_quantile` | Per-group quantile-based outlier removal                                                                                                              |
| `apply_seasonal_q10_q90`   | Robust seasonal Q10–Q90 cleaning per gas, per season, with tunable fence                                                                              |
| `aggregate_reps`           | Collapse field replicates into one row per sampling point (mean/median)                                                                               |

## Schema validator (`src/schema.py`)

`SCHEMA_SPECS` declares 15 expected columns tiered as **required**,
**recommended** or **optional**, each with an expected dtype
(`numeric`/`datetime`/`categorical`) and the feature it powers.
`validate_dataframe(df) -> ValidationResult` returns a row-by-row report and
also flags out-of-range latitude/longitude and the presence of sentinel
values (`±9999`, `±10000`).

## State (`src/state.py`)

Three keys in `st.session_state`:

- `df_raw` — raw upload (after sheet selection).
- `df_processed` — current pipeline output (defaults to `df_raw.copy()`).
- `df_report` — step-by-step report dataframe.

Plus auth keys when Supabase is enabled.

## i18n (`src/i18n/`)

`t("key.path", **kwargs)` resolves keys against `pt.json`, falling back to the
key string when missing. All three locales must stay in parity (471 keys at
v1.0). Use `python -m scripts.i18n_audit` to check.

## Spatial implementation notes

The Spatial page uses the following dependencies:

- `geopandas` + `shapely`: vectors, reprojection (UTM grid).
- `geobr.read_municipality(code_muni=5218805, year=2020)`: Rio Verde
  boundary, cached with `@st.cache_data`. Requires internet on first use.
- `libpysal.weights.KNN`: k-nearest-neighbour spatial weights.
- `esda.moran.{Moran, Moran_Local}`, `esda.getisord.G_Local`: global and
  local autocorrelation.
- `scipy.optimize.least_squares`: variogram fitting (manual ordinary kriging).

The UTM EPSG code is computed from the mean longitude
(`32700 + zone` for the southern hemisphere), so the page works elsewhere in
South America without code changes.

## Testing

`tests/` uses pytest:

- `test_pipeline.py` — covers the original cleaning primitives.
- `test_schema.py` — schema-validator coverage (full schema, missing
  required/recommended/optional, type mismatch, sentinels, lat/lon ranges,
  empty dataframe).
- `test_seasonal_q.py` — Q10–Q90 cleaning (extreme values, NaN preservation,
  fence-factor strictness, group independence, edge cases).

40 tests total at v1.0.
