"""Validação do schema esperado para o dataset de fluxos do solo.

Define três tiers de colunas:

* **required** — sem essas colunas, partes essenciais do app não funcionam.
  Não causam falha; são reportadas com severidade alta.
* **recommended** — habilitam análises padrão (EDA, pipeline default,
  regressão padrão). Reportadas com severidade média.
* **optional** — habilitam funcionalidades específicas (espacial, temporal,
  N₂O, Mata vs Outros). Reportadas com severidade informativa.

A função :func:`validate_dataframe` retorna um relatório estruturado que pode
ser renderizado na Upload page sem alterar o fluxo de carregamento.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ColumnSpec:
    """Especificação de uma coluna esperada."""

    candidates: tuple[str, ...]  # nomes alternativos aceitos
    label: str
    tier: str  # "required" | "recommended" | "optional"
    expected_type: str  # "numeric" | "categorical" | "datetime"
    feature: str  # módulo/feature que depende dessa coluna
    notes: str = ""


# Schema de referência baseado nos exports LI-COR LI-7810SC + Smart Chamber.
SCHEMA_SPECS: tuple[ColumnSpec, ...] = (
    ColumnSpec(
        ("FCO2_DRY", "CO2_Flux"),
        "Fluxo de CO₂",
        tier="required",
        expected_type="numeric",
        feature="EDA, Regressão, Modelagem, Comparativa",
    ),
    ColumnSpec(
        ("FCH4_DRY", "CH4_Flux"),
        "Fluxo de CH₄",
        tier="recommended",
        expected_type="numeric",
        feature="EDA, Regressão, Modelagem",
    ),
    ColumnSpec(
        ("FN2O", "N2O_Flux"),
        "Fluxo de N₂O",
        tier="optional",
        expected_type="numeric",
        feature="EDA estendida (LI-7820)",
    ),
    ColumnSpec(
        ("TS_2 initial_value", "Soil_Temp", "TS"),
        "Temperatura do solo",
        tier="recommended",
        expected_type="numeric",
        feature="Regressão padrão, Comparativa log-linear",
    ),
    ColumnSpec(
        ("SWC_2 initial_value", "Soil_Moist", "SWC"),
        "Umidade do solo",
        tier="recommended",
        expected_type="numeric",
        feature="Regressão padrão, EDA",
    ),
    ColumnSpec(
        ("LATITUDE", "Latitude", "latitude"),
        "Latitude",
        tier="optional",
        expected_type="numeric",
        feature="Análise Espacial, mapa Rio Verde, IDW, Moran, Kriging",
    ),
    ColumnSpec(
        ("LONGITUDE", "Longitude", "longitude"),
        "Longitude",
        tier="optional",
        expected_type="numeric",
        feature="Análise Espacial, mapa Rio Verde, IDW, Moran, Kriging",
    ),
    ColumnSpec(
        ("DIAGNOSTIC initial_value", "Diagnostic Initial_value", "DIAG initial_value"),
        "Flag de diagnóstico",
        tier="recommended",
        expected_type="numeric",
        feature="Pipeline (filtro diagnóstico)",
    ),
    ColumnSpec(
        ("FCO2_DRY R2", "FCO2_DRY LIN_R2"),
        "R² do ajuste de CO₂",
        tier="recommended",
        expected_type="numeric",
        feature="Pipeline (filtro R²)",
    ),
    ColumnSpec(
        ("FCH4_DRY LIN_R2", "FCH4_DRY R2"),
        "R² do ajuste de CH₄",
        tier="optional",
        expected_type="numeric",
        feature="Pipeline (filtro R²)",
    ),
    ColumnSpec(
        ("REP", "Rep"),
        "Identificador de réplica",
        tier="optional",
        expected_type="numeric",
        feature="Pipeline (agregação de réplicas)",
    ),
    ColumnSpec(
        ("DATE_TIME initial_value", "Data", "Date", "DATE", "Date_Time", "DateTime"),
        "Data ou data/hora",
        tier="recommended",
        expected_type="datetime",
        feature="Série Temporal, Comparativa horária",
    ),
    ColumnSpec(
        ("Cultura", "Crop_Type", "cultura"),
        "Cultura ou tipo de uso",
        tier="recommended",
        expected_type="categorical",
        feature="EDA, Comparativa, Modelagem",
    ),
    ColumnSpec(
        ("Fazenda", "Coll_Cluster", "fazenda"),
        "Fazenda / cluster",
        tier="optional",
        expected_type="categorical",
        feature="EDA, Hotspots ranking",
    ),
    ColumnSpec(
        ("Estação", "Época", "Season", "Estacao"),
        "Estação do ano",
        tier="optional",
        expected_type="categorical",
        feature="Pipeline Q10-Q90, EDA Inferência, Spatial faceta",
    ),
)


@dataclass
class ValidationResult:
    rows: list[dict]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def required_missing(self) -> list[str]:
        return [r["label"] for r in self.rows if r["tier"] == "required" and r["status"] == "missing"]

    @property
    def recommended_missing(self) -> list[str]:
        return [r["label"] for r in self.rows if r["tier"] == "recommended" and r["status"] == "missing"]

    @property
    def has_blocking_issues(self) -> bool:
        return bool(self.required_missing) or bool(self.errors)


def _first_existing(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _check_type(series: pd.Series, expected: str) -> tuple[bool, str]:
    if expected == "numeric":
        if pd.api.types.is_numeric_dtype(series):
            return True, "numeric"
        coerced = pd.to_numeric(series, errors="coerce")
        if coerced.notna().sum() / max(len(series), 1) >= 0.9:
            return True, "numeric (coercível)"
        return False, str(series.dtype)
    if expected == "datetime":
        if pd.api.types.is_datetime64_any_dtype(series):
            return True, "datetime"
        coerced = pd.to_datetime(series, errors="coerce")
        if coerced.notna().sum() / max(len(series), 1) >= 0.9:
            return True, "datetime (coercível)"
        return False, str(series.dtype)
    if expected == "categorical":
        return not pd.api.types.is_numeric_dtype(series) or series.nunique(dropna=True) <= 30, str(series.dtype)
    return True, str(series.dtype)


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    rows: list[dict] = []
    warnings: list[str] = []
    errors: list[str] = []

    for spec in SCHEMA_SPECS:
        found = _first_existing(df, spec.candidates)
        if found is None:
            rows.append({
                "label": spec.label,
                "expected": " | ".join(spec.candidates),
                "found": None,
                "tier": spec.tier,
                "status": "missing",
                "type_ok": None,
                "type_found": None,
                "feature": spec.feature,
            })
            continue

        ok, dtype = _check_type(df[found], spec.expected_type)
        rows.append({
            "label": spec.label,
            "expected": " | ".join(spec.candidates),
            "found": found,
            "tier": spec.tier,
            "status": "present" if ok else "type_mismatch",
            "type_ok": ok,
            "type_found": dtype,
            "feature": spec.feature,
        })
        if not ok:
            warnings.append(
                f"Coluna '{found}' encontrada para {spec.label} mas o tipo não é {spec.expected_type} ({dtype})."
            )

    lat = _first_existing(df, ("Latitude",))
    lon = _first_existing(df, ("Longitude",))
    if lat and lon:
        try:
            lat_num = pd.to_numeric(df[lat], errors="coerce").dropna()
            lon_num = pd.to_numeric(df[lon], errors="coerce").dropna()
            if not lat_num.empty and not (-90 <= lat_num.min() <= lat_num.max() <= 90):
                errors.append("Latitude fora do intervalo [-90, 90].")
            if not lon_num.empty and not (-180 <= lon_num.min() <= lon_num.max() <= 180):
                errors.append("Longitude fora do intervalo [-180, 180].")
        except Exception:
            pass

    sentinel_values = {-9999, -10000, 9999, 10000}
    suspicious_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        col_vals = df[col].dropna()
        if col_vals.empty:
            continue
        hits = col_vals.isin(sentinel_values).sum()
        if hits > 0:
            suspicious_cols.append((col, int(hits)))
    if suspicious_cols:
        joined = ", ".join(f"{name} ({n})" for name, n in suspicious_cols[:10])
        warnings.append(f"Possíveis sentinelas (-9999/-10000/9999/10000) presentes em: {joined}.")

    return ValidationResult(rows=rows, warnings=warnings, errors=errors)
