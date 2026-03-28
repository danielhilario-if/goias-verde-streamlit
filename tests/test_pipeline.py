"""
Testes unitários para src/pipeline.py

Rode com:
    source .venv/bin/activate
    pytest tests/ -v
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.pipeline import (
    StepLog,
    aggregate_reps,
    apply_diagnostic_filter,
    apply_r2_threshold,
    build_step_report,
    filter_outliers_quantile,
    find_first_existing,
    remove_columns,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_df(**kwargs) -> pd.DataFrame:
    return pd.DataFrame(kwargs)


# ─── find_first_existing ──────────────────────────────────────────────────────

class TestFindFirstExisting:
    def test_exact_match(self):
        df = _make_df(A=[1], B=[2])
        assert find_first_existing(df, ["A"]) == "A"

    def test_case_insensitive(self):
        df = _make_df(FCO2_DRY=[1])
        assert find_first_existing(df, ["fco2_dry"]) == "FCO2_DRY"

    def test_first_candidate_wins(self):
        df = _make_df(B=[1], A=[2])
        assert find_first_existing(df, ["A", "B"]) == "A"

    def test_not_found_returns_none(self):
        df = _make_df(X=[1])
        assert find_first_existing(df, ["MISSING"]) is None


# ─── apply_diagnostic_filter ──────────────────────────────────────────────────

class TestApplyDiagnosticFilter:
    def test_keeps_zero_rows(self):
        df = _make_df(diag=[0, 1, 0, 2])
        out, log = apply_diagnostic_filter(df, "diag", keep_value=0)
        assert list(out["diag"]) == [0, 0]
        assert log.before == 4
        assert log.after == 2

    def test_log_step_label(self):
        df = _make_df(diag=[0])
        _, log = apply_diagnostic_filter(df, "diag")
        assert "diag" in log.step


# ─── remove_columns ───────────────────────────────────────────────────────────

class TestRemoveColumns:
    def test_removes_existing_columns(self):
        df = _make_df(A=[1], B=[2], C=[3])
        out, log = remove_columns(df, ["A", "B"])
        assert list(out.columns) == ["C"]
        assert log.before == log.after  # row count unchanged

    def test_ignores_missing_columns(self):
        df = _make_df(A=[1])
        out, log = remove_columns(df, ["MISSING"])
        assert list(out.columns) == ["A"]
        assert "ignorada" in log.step


# ─── apply_r2_threshold ───────────────────────────────────────────────────────

class TestApplyR2Threshold:
    def test_filters_below_threshold(self):
        df = _make_df(**{"FCH4 R2": [0.9, 0.5, 0.8], "val": [1, 2, 3]})
        out, log = apply_r2_threshold(df, 0.7, ["FCH4 R2"], [])
        assert len(out) == 2
        assert 0.5 not in out["FCH4 R2"].values

    def test_no_r2_columns_passthrough(self):
        df = _make_df(val=[1, 2, 3])
        out, log = apply_r2_threshold(df, 0.8, ["MISSING_R2"], [])
        assert len(out) == 3
        assert "sem colunas" in log.step


# ─── filter_outliers_quantile ─────────────────────────────────────────────────

class TestFilterOutliersQuantile:
    def setup_method(self):
        self.df = _make_df(val=list(range(100)))

    def test_removes_tails(self):
        out, _ = filter_outliers_quantile(self.df, ["val"], 0.05, 0.95)
        assert len(out) < 100
        assert out["val"].min() >= 5
        assert out["val"].max() <= 94

    def test_no_valid_columns_passthrough(self):
        out, log = filter_outliers_quantile(self.df, ["MISSING"], 0.05, 0.95)
        assert len(out) == 100
        assert "ignorado" in log.step

    def test_grouped(self):
        df = _make_df(
            group=["A"] * 50 + ["B"] * 50,
            val=list(range(50)) + list(range(50)),
        )
        out, log = filter_outliers_quantile(df, ["val"], 0.05, 0.95, group_col="group")
        assert "group" in log.step


# ─── aggregate_reps ───────────────────────────────────────────────────────────

class TestAggregateReps:
    def test_aggregates_mean(self):
        df = _make_df(
            ID=["A", "A", "B", "B"],
            REP=[1, 2, 1, 2],
            val=[10.0, 20.0, 30.0, 40.0],
        )
        out, log = aggregate_reps(df, rep_col="REP", method="media", group_cols=["ID"])
        assert len(out) == 2
        a_row = out[out["ID"] == "A"].iloc[0]
        assert a_row["val"] == pytest.approx(15.0)

    def test_missing_rep_col(self):
        df = _make_df(ID=["A"], val=[1.0])
        out, log = aggregate_reps(df, rep_col="MISSING", method="media", group_cols=["ID"])
        assert len(out) == 1
        assert "ignorada" in log.step


# ─── build_step_report ────────────────────────────────────────────────────────

class TestBuildStepReport:
    def test_percent_removed(self):
        logs = [StepLog(step="test", before=100, after=80)]
        report = build_step_report(logs)
        assert report.iloc[0]["% removidas"] == pytest.approx(20.0)

    def test_zero_before_no_division_error(self):
        logs = [StepLog(step="empty", before=0, after=0)]
        report = build_step_report(logs)
        assert report.iloc[0]["% removidas"] == 0
