from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src.components.dataset_controls import ensure_raw_dataframe
from src.config.settings import (
    PIPELINE_DIAGNOSTIC_CANDIDATES,
    PIPELINE_DROP_CANDIDATES,
    PIPELINE_GROUP_CANDIDATES,
    PIPELINE_R2_CH4_CANDIDATES,
    PIPELINE_R2_CO2_CANDIDATES,
    PIPELINE_REP_CANDIDATES,
    PIPELINE_THRESHOLD_CANDIDATES,
)
from src.i18n import t, translate_step
from src.pipeline import (
    apply_diagnostic_filter,
    apply_r2_threshold,
    apply_threshold_filter,
    aggregate_reps,
    apply_seasonal_q10_q90,
    build_step_report,
    filter_outliers_quantile,
    find_first_existing,
    remove_columns,
)
from src.state import get_processed_dataframe, get_report_dataframe, set_processed_dataset


def _localized_report(report: pd.DataFrame) -> pd.DataFrame:
    """Aplica traducao de mensagens StepLog e renomeia colunas para o idioma atual."""
    if report.empty:
        return report
    out = report.copy()
    if "Etapa" in out.columns:
        out["Etapa"] = out["Etapa"].astype(str).map(translate_step)
    return out.rename(
        columns={
            "Etapa": t("pipeline.report.col.step"),
            "Linhas antes": t("pipeline.report.col.rows_before"),
            "Linhas depois": t("pipeline.report.col.rows_after"),
            "Removidas": t("pipeline.report.col.removed"),
            "% removidas": t("pipeline.report.col.percent_removed"),
        }
    )


def render():
    st.subheader(t("pipeline.title"))

    df_raw = ensure_raw_dataframe(t("pipeline.warn_no_data"))
    if df_raw is None:
        return

    with st.form("pipeline_form"):
        st.markdown(f"### {t('pipeline.section.drop')}")
        use_drop = st.checkbox(t("pipeline.drop.checkbox"), value=True)
        suggested_drop = [column for column in PIPELINE_DROP_CANDIDATES if column in df_raw.columns]
        drop_columns = st.multiselect(
            t("pipeline.drop.multiselect"),
            options=list(df_raw.columns),
            default=suggested_drop,
            help=t("pipeline.drop.help"),
        )

        st.markdown(f"### {t('pipeline.section.diag')}")
        use_diag = st.checkbox(t("pipeline.diag.checkbox"), value=True)
        diag_default = find_first_existing(df_raw, PIPELINE_DIAGNOSTIC_CANDIDATES)
        diag_options = list(df_raw.columns)
        diag_col = st.selectbox(
            t("pipeline.diag.select"),
            options=diag_options,
            index=diag_options.index(diag_default) if diag_default in diag_options else 0,
        )

        st.markdown(f"### {t('pipeline.section.r2')}")
        use_r2 = st.checkbox(t("pipeline.r2.checkbox"), value=True)
        r2_threshold = st.slider(t("pipeline.r2.slider"), 0.0, 1.0, 0.80, 0.01)

        st.markdown(f"### {t('pipeline.section.threshold')}")
        st.caption(t("pipeline.threshold.caption"))
        use_threshold = st.checkbox(t("pipeline.threshold.checkbox"), value=False)
        numeric_cols_pre = list(df_raw.select_dtypes(include="number").columns)
        threshold_default_cols = [c for c in PIPELINE_THRESHOLD_CANDIDATES if c in numeric_cols_pre]
        threshold_columns = st.multiselect(
            t("pipeline.threshold.columns"),
            options=numeric_cols_pre,
            default=threshold_default_cols,
            help=t("pipeline.threshold.help"),
        )
        threshold_direction_options = [t("pipeline.threshold.dir.ge"), t("pipeline.threshold.dir.le")]
        threshold_direction_label = st.radio(
            t("pipeline.threshold.direction"),
            options=threshold_direction_options,
            horizontal=True,
            index=1,
        )
        threshold_direction = "le" if threshold_direction_label == t("pipeline.threshold.dir.le") else "ge"
        threshold_value = st.number_input(
            t("pipeline.threshold.value"),
            value=0.20,
            step=0.05,
            format="%.4f",
        )

        st.markdown(f"### {t('pipeline.section.outliers')}")
        use_out = st.checkbox(t("pipeline.out.checkbox"), value=True)
        numeric_cols = list(df_raw.select_dtypes(include="number").columns)
        default_out = [column for column in ["FCO2_DRY", "FCH4_DRY"] if column in numeric_cols]
        outlier_columns = st.multiselect(t("pipeline.out.columns"), options=numeric_cols, default=default_out)
        q_min = st.slider(t("pipeline.out.qmin"), 0.0, 0.45, 0.05, 0.01)
        q_max = st.slider(t("pipeline.out.qmax"), 0.50, 1.0, 0.95, 0.01)
        outlier_group_options = [t("pipeline.out.group_global")] + [column for column in df_raw.columns if column not in numeric_cols]
        default_group_label = "Época" if "Época" in outlier_group_options else t("pipeline.out.group_global")
        outlier_group_col = st.selectbox(
            t("pipeline.out.group"),
            options=outlier_group_options,
            index=outlier_group_options.index(default_group_label),
        )

        st.markdown(f"### {t('pipeline.section.seasonal_q')}")
        st.caption(t("pipeline.seasonal_q.caption"))
        use_seasonal_q = st.checkbox(t("pipeline.seasonal_q.checkbox"), value=False)
        seasonal_default_cols = [c for c in ("FCO2_DRY", "FCH4_DRY", "FN2O", "N2O_Flux", "CO2_Flux", "CH4_Flux") if c in numeric_cols]
        seasonal_q_cols = st.multiselect(
            t("pipeline.seasonal_q.columns"),
            options=numeric_cols,
            default=seasonal_default_cols,
        )
        seasonal_options = [c for c in df_raw.columns if c not in numeric_cols]
        seasonal_default_col = "Época" if "Época" in seasonal_options else (seasonal_options[0] if seasonal_options else None)
        seasonal_col = st.selectbox(
            t("pipeline.seasonal_q.season_col"),
            options=seasonal_options or list(df_raw.columns),
            index=seasonal_options.index(seasonal_default_col) if seasonal_default_col in seasonal_options else 0,
        )
        seasonal_k = st.slider(t("pipeline.seasonal_q.fence"), 0.5, 3.0, 1.5, 0.1)

        st.markdown(f"### {t('pipeline.section.rep')}")
        st.caption(t("pipeline.rep.caption"))
        use_rep = st.checkbox(t("pipeline.rep.checkbox"), value=True)
        rep_default = find_first_existing(df_raw, PIPELINE_REP_CANDIDATES)
        rep_col = st.selectbox(
            t("pipeline.rep.column"),
            options=list(df_raw.columns),
            index=list(df_raw.columns).index(rep_default) if rep_default in df_raw.columns else 0,
        )
        rep_method_options = [t("pipeline.rep.method.mean"), t("pipeline.rep.method.median")]
        rep_method_label = st.radio(t("pipeline.rep.method"), options=rep_method_options, horizontal=True)
        rep_method = "media" if rep_method_label == t("pipeline.rep.method.mean") else "mediana"
        default_group = [column for column in PIPELINE_GROUP_CANDIDATES if column in df_raw.columns and column != rep_col]
        rep_group_cols = st.multiselect(
            t("pipeline.rep.group_keys"),
            options=list(df_raw.columns),
            default=default_group,
        )
        st.caption(t("pipeline.rep.tip"))

        apply_btn = st.form_submit_button(t("pipeline.apply_button"), type="primary")

    if apply_btn:
        logs = []
        warnings = []
        df = df_raw.copy()

        if use_drop and drop_columns:
            df, log_item = remove_columns(df, drop_columns)
            logs.append(log_item)

        if use_diag and diag_col in df.columns:
            df, log_item = apply_diagnostic_filter(df, diag_col, keep_value=0)
            logs.append(log_item)
        elif use_diag:
            warnings.append(t("pipeline.warn_diag_missing", col=diag_col))

        if use_r2:
            df, log_item = apply_r2_threshold(
                df,
                threshold=r2_threshold,
                ch4_candidates=PIPELINE_R2_CH4_CANDIDATES,
                co2_candidates=PIPELINE_R2_CO2_CANDIDATES,
            )
            logs.append(log_item)

        if use_threshold:
            valid_threshold_cols = [c for c in threshold_columns if c in df.columns]
            if threshold_columns and not valid_threshold_cols:
                warnings.append(t("pipeline.warn_threshold_no_cols"))
            if valid_threshold_cols:
                df, log_item = apply_threshold_filter(
                    df,
                    columns=valid_threshold_cols,
                    threshold=float(threshold_value),
                    direction=threshold_direction,
                )
                logs.append(log_item)

        if use_out:
            valid_outlier_columns = [column for column in outlier_columns if column in df.columns]
            group_col = None if outlier_group_col == t("pipeline.out.group_global") else outlier_group_col
            if group_col and group_col not in df.columns:
                warnings.append(t("pipeline.warn_outlier_group", col=group_col))
                group_col = None
            if outlier_columns and not valid_outlier_columns:
                warnings.append(t("pipeline.warn_outlier_no_cols"))
            df, log_item = filter_outliers_quantile(df, valid_outlier_columns, q_min, q_max, group_col)
            logs.append(log_item)

        if use_seasonal_q:
            valid_q_cols = [c for c in seasonal_q_cols if c in df.columns]
            if seasonal_col not in df.columns:
                warnings.append(t("pipeline.warn_seasonal_q_missing", col=seasonal_col))
            elif not valid_q_cols:
                warnings.append(t("pipeline.warn_seasonal_q_no_cols"))
            else:
                df, log_item = apply_seasonal_q10_q90(df, valid_q_cols, seasonal_col, fence_factor=seasonal_k)
                logs.append(log_item)

        if use_rep:
            valid_rep_groups = [column for column in rep_group_cols if column in df.columns and column != rep_col]
            if rep_col not in df.columns:
                warnings.append(t("pipeline.warn_rep_missing", col=rep_col))
            elif rep_group_cols and not valid_rep_groups:
                warnings.append(t("pipeline.warn_rep_no_keys"))
            df, log_item = aggregate_reps(df, rep_col=rep_col, method=rep_method, group_cols=valid_rep_groups)
            logs.append(log_item)

        set_processed_dataset(df, build_step_report(logs))
        for message in warnings:
            st.warning(message)
        st.success(t("pipeline.success"))

    df_processed = get_processed_dataframe()
    if df_processed is None:
        df_processed = df_raw
    report = get_report_dataframe()

    c1, c2 = st.columns(2)
    c1.metric(t("pipeline.metric.original"), len(df_raw))
    c2.metric(t("pipeline.metric.processed"), len(df_processed))

    st.markdown(f"#### {t('pipeline.report_title')}")
    if not report.empty:
        st.dataframe(_localized_report(report), use_container_width=True)
    else:
        st.info(t("pipeline.report_empty"))

    st.markdown(f"#### {t('pipeline.preview_title')}")
    st.dataframe(df_processed.head(20), use_container_width=True)

    st.markdown(f"#### {t('pipeline.export_title')}")
    col_csv, col_xlsx = st.columns(2)
    csv_data = df_processed.to_csv(index=False).encode("utf-8-sig")
    col_csv.download_button(
        f"⬇️ {t('pipeline.export_csv')}",
        data=csv_data,
        file_name="dataset_processado_pipeline.csv",
        mime="text/csv",
        use_container_width=True,
    )
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        df_processed.to_excel(writer, index=False, sheet_name="Processado")
    col_xlsx.download_button(
        f"⬇️ {t('pipeline.export_xlsx')}",
        data=xlsx_buffer.getvalue(),
        file_name="dataset_processado_pipeline.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
