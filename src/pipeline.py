from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass
class StepLog:
    step: str
    before: int
    after: int


def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum())


def find_first_existing(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    cols = list(df.columns)
    exact = {c: c for c in cols}
    norm_map = {_norm(c): c for c in cols}

    for cand in candidates:
        if cand in exact:
            return cand
        cand_norm = _norm(cand)
        if cand_norm in norm_map:
            return norm_map[cand_norm]
    return None


def load_uploaded_file(uploaded_file, sheet_name: Optional[str] = None) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        if sheet_name:
            return pd.read_excel(uploaded_file, sheet_name=sheet_name)
        return pd.read_excel(uploaded_file)
    raise ValueError("Formato nao suportado. Envie CSV ou Excel.")


def available_excel_sheets(uploaded_file) -> list[str]:
    name = uploaded_file.name.lower()
    if not (name.endswith(".xlsx") or name.endswith(".xls")):
        return []
    xls = pd.ExcelFile(uploaded_file)
    return list(xls.sheet_names)


def apply_diagnostic_filter(df: pd.DataFrame, col: str, keep_value=0) -> tuple[pd.DataFrame, StepLog]:
    before = len(df)
    out = df[df[col] == keep_value].copy()
    return out, StepLog(step=f"Filtro diagnostico ({col} == {keep_value})", before=before, after=len(out))


def remove_columns(df: pd.DataFrame, columns: Iterable[str]) -> tuple[pd.DataFrame, StepLog]:
    before = len(df)
    valid_cols = [c for c in columns if c in df.columns]
    out = df.drop(columns=valid_cols, errors="ignore").copy()

    if valid_cols:
        step = f"Remocao de variaveis ({len(valid_cols)} colunas)"
    else:
        step = "Remocao de variaveis ignorada (sem colunas validas)"

    return out, StepLog(step=step, before=before, after=len(out))


def apply_r2_threshold(
    df: pd.DataFrame,
    threshold: float,
    ch4_candidates: Iterable[str],
    co2_candidates: Iterable[str],
) -> tuple[pd.DataFrame, StepLog]:
    before = len(df)
    out = df.copy()

    ch4_col = find_first_existing(df, ch4_candidates)
    co2_col = find_first_existing(df, co2_candidates)

    mask = pd.Series(True, index=out.index)
    used = []

    if ch4_col:
        mask &= out[ch4_col] >= threshold
        used.append(ch4_col)

    if co2_col:
        mask &= out[co2_col] >= threshold
        used.append(co2_col)

    out = out[mask].copy()
    label = "Filtro R2"
    if used:
        label += f" ({', '.join(used)} >= {threshold:.2f})"
    else:
        label += " (sem colunas R2 encontradas)"

    return out, StepLog(step=label, before=before, after=len(out))


def aggregate_reps(
    df: pd.DataFrame,
    rep_col: str,
    method: str,
    group_cols: list[str],
) -> tuple[pd.DataFrame, StepLog]:
    before = len(df)

    if rep_col not in df.columns:
        return df.copy(), StepLog(step=f"Agregacao REP ignorada ({rep_col} nao encontrado)", before=before, after=before)

    if not group_cols:
        return df.copy(), StepLog(step="Agregacao REP ignorada (sem chaves de agrupamento)", before=before, after=before)

    valid_group_cols = [c for c in group_cols if c in df.columns and c != rep_col]
    if not valid_group_cols:
        return df.copy(), StepLog(step="Agregacao REP ignorada (chaves invalidas)", before=before, after=before)

    work_df = df.copy()

    # Evita granularidade excessiva em chaves comuns de agrupamento.
    for col in valid_group_cols:
        if pd.api.types.is_datetime64_any_dtype(work_df[col]):
            work_df[col] = work_df[col].dt.date
        elif pd.api.types.is_float_dtype(work_df[col]):
            work_df[col] = work_df[col].round(6)

    agg_func = "median" if method == "mediana" else "mean"

    numeric_cols = [
        c for c in work_df.select_dtypes(include=[np.number]).columns if c != rep_col and c not in valid_group_cols
    ]
    other_cols = [c for c in work_df.columns if c not in valid_group_cols and c not in numeric_cols and c != rep_col]

    agg_map = {c: agg_func for c in numeric_cols}
    agg_map.update({c: "first" for c in other_cols})

    grouped = work_df.groupby(valid_group_cols, dropna=False, as_index=False)
    out = grouped.agg(agg_map)

    rep_count_col = "N_REPS"
    if rep_count_col in out.columns:
        rep_count_col = "N_REPS_AGG"
    counts = grouped.size().rename(columns={"size": rep_count_col})
    out = out.merge(counts, on=valid_group_cols, how="left")

    n_groups_multi = int((out[rep_count_col] > 1).sum())
    step = f"Agregacao de repeticoes por {agg_func} ({n_groups_multi} grupos com N_REPS>1)"
    return out, StepLog(step=step, before=before, after=len(out))


def filter_outliers_quantile(
    df: pd.DataFrame,
    columns: list[str],
    q_min: float,
    q_max: float,
    group_col: Optional[str] = None,
) -> tuple[pd.DataFrame, StepLog]:
    before = len(df)
    out = df.copy()

    valid_cols = [c for c in columns if c in out.columns]
    if not valid_cols:
        return out, StepLog(step="Outliers ignorado (sem colunas validas)", before=before, after=len(out))

    if group_col and group_col in out.columns:
        mask = pd.Series(True, index=out.index)
        for col in valid_cols:
            low = out.groupby(group_col)[col].transform(lambda s: s.quantile(q_min))
            high = out.groupby(group_col)[col].transform(lambda s: s.quantile(q_max))
            mask &= out[col].between(low, high)
        out = out[mask].copy()
        step = f"Outliers por quantil ({q_min:.2f}-{q_max:.2f}) por {group_col}"
    else:
        mask = pd.Series(True, index=out.index)
        for col in valid_cols:
            low = out[col].quantile(q_min)
            high = out[col].quantile(q_max)
            mask &= out[col].between(low, high)
        out = out[mask].copy()
        step = f"Outliers por quantil ({q_min:.2f}-{q_max:.2f}) global"

    return out, StepLog(step=step, before=before, after=len(out))


def build_step_report(logs: list[StepLog]) -> pd.DataFrame:
    rows = []
    for item in logs:
        removed = item.before - item.after
        rows.append(
            {
                "Etapa": item.step,
                "Linhas antes": item.before,
                "Linhas depois": item.after,
                "Removidas": removed,
                "% removidas": (removed / item.before * 100) if item.before else 0,
            }
        )
    return pd.DataFrame(rows)
