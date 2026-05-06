"""Testes unitários para apply_seasonal_q10_q90 em src/pipeline.py."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.pipeline import apply_seasonal_q10_q90


def _seasonal_dataset(extreme_indices: list[int] | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n_per_season = 50
    rows = []
    for season, mu in [("Verão", 3.0), ("Inverno", 1.5), ("Primavera", 2.5), ("Outono", 2.0)]:
        for _ in range(n_per_season):
            rows.append({"Season": season, "FCO2_DRY": float(rng.normal(mu, 0.4))})
    df = pd.DataFrame(rows)
    if extreme_indices:
        for idx in extreme_indices:
            df.loc[idx, "FCO2_DRY"] = 100.0
    return df


class TestSeasonalQ10Q90Filtering:
    def test_extreme_values_are_removed(self):
        df = _seasonal_dataset(extreme_indices=[0, 50])
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        assert log.before == 200
        assert log.after < log.before
        assert (out["FCO2_DRY"] == 100.0).sum() == 0

    def test_no_extremes_keeps_most_rows(self):
        df = _seasonal_dataset()
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        kept_ratio = log.after / log.before
        assert kept_ratio > 0.85

    def test_fence_factor_affects_strictness(self):
        df = _seasonal_dataset(extreme_indices=[0])
        out_strict, log_strict = apply_seasonal_q10_q90(
            df, columns=["FCO2_DRY"], season_col="Season", fence_factor=0.5
        )
        out_loose, log_loose = apply_seasonal_q10_q90(
            df, columns=["FCO2_DRY"], season_col="Season", fence_factor=3.0
        )
        assert log_strict.after <= log_loose.after


class TestSeasonalQ10Q90NanHandling:
    def test_nan_rows_are_kept(self):
        df = pd.DataFrame({
            "Season": ["Verão", "Verão", "Verão", "Verão", "Verão"] * 5,
            "FCO2_DRY": ([2.0, 2.5, 3.0, 2.2, np.nan]) * 5,
        })
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        nan_count_before = df["FCO2_DRY"].isna().sum()
        nan_count_after = out["FCO2_DRY"].isna().sum()
        assert nan_count_after == nan_count_before


class TestSeasonalQ10Q90EdgeCases:
    def test_missing_season_column_is_skipped(self):
        df = pd.DataFrame({"FCO2_DRY": [1.0, 2.0, 3.0]})
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Estacao", fence_factor=1.5)
        assert log.before == log.after == 3
        assert "ignorada" in log.step.lower() or "sem coluna" in log.step.lower()

    def test_missing_target_columns_are_skipped(self):
        df = pd.DataFrame({"Season": ["A", "B"], "outra": [1.0, 2.0]})
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        assert log.before == log.after == 2
        assert "ignorada" in log.step.lower() or "validas" in log.step.lower()

    def test_subset_of_columns_are_used(self):
        df = pd.DataFrame({
            "Season": ["A"] * 20 + ["B"] * 20,
            "FCO2_DRY": ([2.0] * 19 + [100.0]) + ([2.0] * 19 + [100.0]),
            "ignored": list(range(40)),
        })
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        assert log.after < log.before


class TestSeasonalQ10Q90PerSeasonIndependence:
    def test_groups_have_independent_thresholds(self):
        df = pd.DataFrame({
            "Season": (["A"] * 20) + (["B"] * 20),
            "FCO2_DRY": list(np.full(20, 1.0)) + list(np.full(20, 100.0)),
        })
        df.loc[0, "FCO2_DRY"] = 50.0
        df.loc[20, "FCO2_DRY"] = 50.0
        out, log = apply_seasonal_q10_q90(df, columns=["FCO2_DRY"], season_col="Season", fence_factor=1.5)
        assert log.after < log.before
