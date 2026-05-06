# Data Dictionary

This document describes the reference column schema that the ChamberFlux application validates uploaded datasets against. It is derived from the canonical `ColumnSpec` declarations in [`src/schema.py`](../src/schema.py); update this file whenever `SCHEMA_SPECS` changes.

The schema is modelled on the tabular CSV/XLSX export produced by the LI-COR LI-7810SC trace gas analyzer combined with the 8200-01S Smart Chamber, and on the LI-7820 N₂O/H₂O analyzer. Datasets that do not originate from these instruments are accepted as long as they expose columns with one of the recognised candidate names.

## Severity tiers

Every expected column is classified into one of three tiers. Missing columns never block the upload — they only disable the dependent features.

| Tier          | What it means | Reporting severity                                |
|---------------|---|---|
| `required`    | Without this column, the core analytical flow does not function. | High — flagged conspicuously in the validation report. |
| `recommended` | Required by standard EDA, the default cleaning pipeline and the default regression presets. | Medium — flagged but does not block features that do not depend on it. |
| `optional`    | Enables specific features (Spatial Analysis, Time Series, N₂O extension, Two-group comparison). | Informational — silently disables the corresponding tab. |

## Column reference

The application looks for each canonical column under one or more candidate names. The first candidate that matches an actual column header in the uploaded dataset is used; if none match, the column is reported as `missing` for its tier.

### Numeric columns

| Canonical name | Candidates                                                | Tier        | Dependent features                                                                       |
|---|---|---|---|
| Fluxo de CO₂            | `FCO2_DRY`, `CO2_Flux`                                    | required    | EDA, Regression, Modeling, Two-group comparison                                          |
| Fluxo de CH₄            | `FCH4_DRY`, `CH4_Flux`                                    | recommended | EDA, Regression, Modeling                                                                |
| Fluxo de N₂O            | `FN2O`, `N2O_Flux`                                        | optional    | Extended EDA (LI-7820)                                                                   |
| Soil temperature        | `TS_2 initial_value`, `Soil_Temp`, `TS`                   | recommended | Default regression presets, Two-group log-linear comparison                              |
| Soil water content      | `SWC_2 initial_value`, `Soil_Moist`, `SWC`                | recommended | Default regression presets, EDA                                                          |
| Latitude                | `LATITUDE`, `Latitude`, `latitude`                        | optional    | Spatial Analysis, Rio Verde basemap, IDW, Moran's I, ordinary kriging                    |
| Longitude               | `LONGITUDE`, `Longitude`, `longitude`                     | optional    | Spatial Analysis, Rio Verde basemap, IDW, Moran's I, ordinary kriging                    |
| Diagnostic flag         | `DIAGNOSTIC initial_value`, `Diagnostic Initial_value`, `DIAG initial_value` | recommended | Pipeline (diagnostic filter)                                                             |
| R² of the CO₂ fit       | `FCO2_DRY R2`, `FCO2_DRY LIN_R2`                          | recommended | Pipeline (R² threshold filter)                                                           |
| R² of the CH₄ fit       | `FCH4_DRY LIN_R2`, `FCH4_DRY R2`                          | optional    | Pipeline (R² threshold filter)                                                           |
| Replicate index         | `REP`, `Rep`                                              | optional    | Pipeline (replicate aggregation)                                                         |

### Datetime columns

| Canonical name | Candidates | Tier | Dependent features |
|---|---|---|---|
| Date or date/time | `DATE_TIME initial_value`, `Data`, `Date`, `DATE`, `Date_Time`, `DateTime` | recommended | Time Series, Two-group hourly comparison |

### Categorical columns

| Canonical name | Candidates                              | Tier        | Dependent features                                              |
|---|---|---|---|
| Crop or land use      | `Cultura`, `Crop_Type`, `cultura`        | recommended | EDA, Two-group comparison, Modeling                             |
| Farm / cluster        | `Fazenda`, `Coll_Cluster`, `fazenda`     | optional    | EDA, Hotspots ranking                                           |
| Season                | `Estação`, `Época`, `Season`, `Estacao`  | optional    | Pipeline Q10–Q90 fence, EDA Inference, Spatial faceting          |

## Validation logic

Beyond column presence, the validator (`validate_dataframe` in `src/schema.py`) performs three additional checks:

1. **Type coercion test.** Numeric columns are accepted if they are already of a numeric dtype, or if at least 90 % of the values can be coerced via `pd.to_numeric(errors="coerce")`. Datetime columns are accepted under the analogous criterion with `pd.to_datetime`. Categorical columns are accepted if they are non-numeric or if their cardinality is at most 30 distinct values.
2. **Coordinate range check.** When both `Latitude` and `Longitude` columns are present, the validator confirms that latitude lies in `[-90, 90]` and longitude lies in `[-180, 180]`. Out-of-range values raise a blocking validation error.
3. **Sentinel-value scan.** Every numeric column is scanned for the LI-COR sentinel values `-9999`, `-10000`, `9999`, `10000`. If any are present, the validator emits a warning listing the offending columns; users are expected to coerce these to `NaN` before relying on the values.

## Adding or modifying columns

To extend the schema for a new instrument or a derived dataset, edit `src/schema.py` and add a new `ColumnSpec` entry to the `SCHEMA_SPECS` tuple. Each entry follows the structure:

```python
ColumnSpec(
    candidates=("CANONICAL_NAME", "alternate_name", "lowercase_name"),
    label="Human-readable label (Portuguese, used in the validation UI)",
    tier="required" | "recommended" | "optional",
    expected_type="numeric" | "categorical" | "datetime",
    feature="Module or page that depends on this column",
    notes="(optional) free-form explanation",
)
```

After editing, regenerate this document so it reflects the live schema. The unit tests in `tests/test_schema.py` exercise both presence and type checks and should be extended whenever a new tier-`required` column is introduced.

## Sentinel and edge cases

- **Empty cells** in numeric columns are treated as `NaN` after coercion and are skipped by the cleaning pipeline filters that operate on non-null values.
- **Mixed-case column names** are tolerated only via the explicit candidate aliases listed above; the validator does not perform fuzzy matching beyond the declared aliases.
- **Datetime columns with mixed formats** are coerced with `pd.to_datetime(errors="coerce")`; rows whose date cannot be parsed are kept in the dataset but excluded from the Time Series and hourly-pattern analyses.
- **Latitude/longitude with comma decimals** (e.g., `-17,75`) must be converted to dot decimals (`-17.75`) before upload — the validator does not coerce locale-specific number formats.

## See also

- [`src/schema.py`](../src/schema.py) — canonical source of the schema specifications
- [`docs/architecture.md`](architecture.md) — overall application architecture
- [`tests/test_schema.py`](../tests/test_schema.py) — unit tests for the validator
- LI-COR LI-7810SC technical reference and 8200-01S Smart Chamber documentation
