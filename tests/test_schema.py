"""Testes unitários para src/schema.py."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.schema import SCHEMA_SPECS, validate_dataframe


def _full_dataset(n: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "FCO2_DRY": rng.normal(2.5, 0.6, n),
        "FCH4_DRY": rng.normal(0.0, 0.05, n),
        "TS_2 initial_value": rng.normal(25, 3, n),
        "SWC_2 initial_value": rng.uniform(0.1, 0.4, n),
        "Latitude": rng.uniform(-17.9, -17.7, n),
        "Longitude": rng.uniform(-51.0, -50.8, n),
        "Diagnostic Initial_value": rng.integers(0, 2, n),
        "FCO2_DRY R2": rng.uniform(0.8, 1.0, n),
        "FCH4_DRY LIN_R2": rng.uniform(0.7, 1.0, n),
        "REP": rng.integers(1, 4, n),
        "Data": pd.date_range("2024-04-01", periods=n, freq="D"),
        "Cultura": rng.choice(["Soja", "Milho", "Mata"], n),
        "Fazenda": rng.choice(["F1", "F2"], n),
        "Época": rng.choice(["Verão", "Inverno"], n),
    })


class TestValidateDataframeFullSchema:
    def test_full_schema_marks_all_present(self):
        df = _full_dataset()
        result = validate_dataframe(df)
        assert result.required_missing == []
        assert result.recommended_missing == []
        statuses = {r["label"]: r["status"] for r in result.rows}
        assert statuses["Fluxo de CO₂"] == "present"
        assert statuses["Latitude"] == "present"

    def test_no_blocking_issues_on_full_dataset(self):
        df = _full_dataset()
        result = validate_dataframe(df)
        assert not result.has_blocking_issues


class TestValidateDataframeMissingColumns:
    def test_missing_required_column_is_reported(self):
        df = _full_dataset().drop(columns=["FCO2_DRY"])
        result = validate_dataframe(df)
        assert "Fluxo de CO₂" in result.required_missing
        assert result.has_blocking_issues

    def test_missing_recommended_does_not_block(self):
        df = _full_dataset().drop(columns=["TS_2 initial_value"])
        result = validate_dataframe(df)
        assert "Temperatura do solo" in result.recommended_missing
        assert not result.has_blocking_issues

    def test_optional_missing_is_silent(self):
        df = _full_dataset().drop(columns=["Latitude", "Longitude"])
        result = validate_dataframe(df)
        latitude_status = next(r["status"] for r in result.rows if r["label"] == "Latitude")
        longitude_status = next(r["status"] for r in result.rows if r["label"] == "Longitude")
        assert latitude_status == "missing"
        assert longitude_status == "missing"
        assert "Latitude" not in result.required_missing
        assert "Latitude" not in result.recommended_missing


class TestValidateDataframeAlternativeNames:
    def test_accepts_co2_flux_synonym(self):
        df = _full_dataset().rename(columns={"FCO2_DRY": "CO2_Flux"})
        result = validate_dataframe(df)
        assert "Fluxo de CO₂" not in result.required_missing
        co2_row = next(r for r in result.rows if r["label"] == "Fluxo de CO₂")
        assert co2_row["found"] == "CO2_Flux"

    def test_accepts_n2o_optional_synonym(self):
        df = _full_dataset()
        df["N2O_Flux"] = 0.001
        result = validate_dataframe(df)
        n2o_row = next(r for r in result.rows if r["label"] == "Fluxo de N₂O")
        assert n2o_row["status"] == "present"
        assert n2o_row["found"] == "N2O_Flux"


class TestValidateDataframeTypeChecking:
    def test_string_co2_flagged_as_type_mismatch(self):
        df = _full_dataset()
        df["FCO2_DRY"] = ["abc"] * len(df)
        result = validate_dataframe(df)
        co2_row = next(r for r in result.rows if r["label"] == "Fluxo de CO₂")
        assert co2_row["status"] == "type_mismatch"
        assert any("FCO2_DRY" in w for w in result.warnings)

    def test_coercible_numeric_passes(self):
        df = _full_dataset()
        df["FCO2_DRY"] = df["FCO2_DRY"].astype(str)
        result = validate_dataframe(df)
        co2_row = next(r for r in result.rows if r["label"] == "Fluxo de CO₂")
        assert co2_row["status"] == "present"


class TestValidateDataframeCoordinateRanges:
    def test_latitude_out_of_range_flags_error(self):
        df = _full_dataset()
        df.loc[0, "Latitude"] = 200.0
        result = validate_dataframe(df)
        assert any("Latitude" in e for e in result.errors)

    def test_longitude_out_of_range_flags_error(self):
        df = _full_dataset()
        df.loc[0, "Longitude"] = -500.0
        result = validate_dataframe(df)
        assert any("Longitude" in e for e in result.errors)

    def test_valid_brazilian_coordinates_pass(self):
        df = _full_dataset()
        result = validate_dataframe(df)
        assert result.errors == []


class TestValidateDataframeSentinelDetection:
    def test_sentinel_minus_9999_is_warned(self):
        df = _full_dataset()
        df.loc[0, "FCO2_DRY"] = -9999
        result = validate_dataframe(df)
        assert any("sentinela" in w.lower() or "FCO2_DRY" in w for w in result.warnings)

    def test_no_sentinel_no_warning(self):
        df = _full_dataset()
        result = validate_dataframe(df)
        sentinel_warnings = [w for w in result.warnings if "sentinela" in w.lower()]
        assert sentinel_warnings == []


class TestValidateDataframeEmpty:
    def test_empty_dataframe_marks_all_missing(self):
        df = pd.DataFrame()
        result = validate_dataframe(df)
        assert all(r["status"] == "missing" for r in result.rows)
        assert result.required_missing  # at least one required is missing
        assert len(result.rows) == len(SCHEMA_SPECS)
