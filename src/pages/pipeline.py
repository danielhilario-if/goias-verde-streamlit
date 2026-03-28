from __future__ import annotations

import io
import json

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
)
from src.pipeline import (
    apply_diagnostic_filter,
    apply_r2_threshold,
    aggregate_reps,
    build_step_report,
    filter_outliers_quantile,
    find_first_existing,
    remove_columns,
)
from src.state import get_processed_dataframe, get_report_dataframe, set_processed_dataset


def render():
    st.subheader("Pipeline e Processamento")

    df_raw = ensure_raw_dataframe("Carregue um arquivo na aba Upload antes de processar.")
    if df_raw is None:
        return

    with st.form("pipeline_form"):
        st.markdown("### 0) Remoção de variaveis")
        use_drop = st.checkbox("Aplicar remoção de features", value=True)
        suggested_drop = [column for column in PIPELINE_DROP_CANDIDATES if column in df_raw.columns]
        drop_columns = st.multiselect(
            "Variaveis para remover antes do processamento",
            options=list(df_raw.columns),
            default=suggested_drop,
            help="As colunas selecionadas serao removidas no inicio do pipeline.",
        )

        st.markdown("### 1) Filtro Diagnóstico")
        use_diag = st.checkbox("Aplicar filtro Diagnostic == 0", value=True)
        diag_default = find_first_existing(df_raw, PIPELINE_DIAGNOSTIC_CANDIDATES)
        diag_options = list(df_raw.columns)
        diag_col = st.selectbox(
            "Coluna de diagnostico",
            options=diag_options,
            index=diag_options.index(diag_default) if diag_default in diag_options else 0,
        )

        st.markdown("### 2) Filtro por Limiar de R2")
        use_r2 = st.checkbox("Aplicar filtro de R2", value=True)
        r2_threshold = st.slider("Limiar Mínimo de R2", 0.0, 1.0, 0.80, 0.01)

        st.markdown("### 3) Outliers por quantis")
        use_out = st.checkbox("Aplicar filtro de outliers", value=True)
        numeric_cols = list(df_raw.select_dtypes(include="number").columns)
        default_out = [column for column in ["FCO2_DRY", "FCH4_DRY"] if column in numeric_cols]
        outlier_columns = st.multiselect("Colunas para outlier", options=numeric_cols, default=default_out)
        q_min = st.slider("Quantil minimo", 0.0, 0.45, 0.05, 0.01)
        q_max = st.slider("Quantil maximo", 0.50, 1.0, 0.95, 0.01)
        outlier_group_options = ["(global)"] + [column for column in df_raw.columns if column not in numeric_cols]
        default_group_col = "Época" if "Época" in outlier_group_options else "(global)"
        outlier_group_col = st.selectbox(
            "Outlier por grupo",
            options=outlier_group_options,
            index=outlier_group_options.index(default_group_col),
        )

        st.markdown("### 4) Agregação de repetições (REP)")
        st.caption("A agregação é aplicada após os filtros para calcular a média/mediana das repetições remanescentes.")
        use_rep = st.checkbox("Agregar repetições", value=True)
        rep_default = find_first_existing(df_raw, PIPELINE_REP_CANDIDATES)
        rep_col = st.selectbox(
            "Coluna de repetição",
            options=list(df_raw.columns),
            index=list(df_raw.columns).index(rep_default) if rep_default in df_raw.columns else 0,
        )
        rep_method = st.radio("Método", options=["media", "mediana"], horizontal=True)
        default_group = [column for column in PIPELINE_GROUP_CANDIDATES if column in df_raw.columns and column != rep_col]
        rep_group_cols = st.multiselect(
            "Chaves de Agrupamento (sem REP)",
            options=list(df_raw.columns),
            default=default_group,
        )
        st.caption("Dica: evite usar Latitude/Longitude como chave se elas variam entre REP_1/REP_2/REP_3.")

        apply_btn = st.form_submit_button("Aplicar pipeline", type="primary")

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
            warnings.append(f"Filtro diagnostico ignorado: coluna '{diag_col}' nao encontrada (pode ter sido removida).")

        if use_r2:
            df, log_item = apply_r2_threshold(
                df,
                threshold=r2_threshold,
                ch4_candidates=PIPELINE_R2_CH4_CANDIDATES,
                co2_candidates=PIPELINE_R2_CO2_CANDIDATES,
            )
            logs.append(log_item)

        if use_out:
            valid_outlier_columns = [column for column in outlier_columns if column in df.columns]
            group_col = None if outlier_group_col == "(global)" else outlier_group_col
            if group_col and group_col not in df.columns:
                warnings.append(f"Outliers por grupo ajustado para global: coluna '{group_col}' foi removida.")
                group_col = None
            if outlier_columns and not valid_outlier_columns:
                warnings.append("Filtro de outliers ignorado: todas as colunas selecionadas foram removidas.")
            df, log_item = filter_outliers_quantile(df, valid_outlier_columns, q_min, q_max, group_col)
            logs.append(log_item)

        if use_rep:
            valid_rep_groups = [column for column in rep_group_cols if column in df.columns and column != rep_col]
            if rep_col not in df.columns:
                warnings.append(f"Agregacao de repeticoes ignorada: coluna REP '{rep_col}' foi removida.")
            elif rep_group_cols and not valid_rep_groups:
                warnings.append("Agregacao de repeticoes sem chaves validas apos remocao de colunas.")
            df, log_item = aggregate_reps(df, rep_col=rep_col, method=rep_method, group_cols=valid_rep_groups)
            logs.append(log_item)

        set_processed_dataset(df, build_step_report(logs))
        for message in warnings:
            st.warning(message)
        st.success("Pipeline aplicado com sucesso.")

    df_processed = get_processed_dataframe()
    if df_processed is None:
        df_processed = df_raw
    report = get_report_dataframe()

    c1, c2 = st.columns(2)
    c1.metric("Linhas original", len(df_raw))
    c2.metric("Linhas processadas", len(df_processed))

    st.markdown("#### Relatorio de etapas")
    if not report.empty:
        st.dataframe(report, width="stretch")
    else:
        st.info("Aplique o pipeline para gerar o relatorio.")

    st.markdown("#### Preview do processado")
    st.dataframe(df_processed.head(20), width="stretch")

    st.markdown("#### Exportar dataset processado")
    col_csv, col_xlsx = st.columns(2)
    csv_data = df_processed.to_csv(index=False).encode("utf-8-sig")
    col_csv.download_button(
        "⬇️ Baixar CSV",
        data=csv_data,
        file_name="dataset_processado_pipeline.csv",
        mime="text/csv",
        use_container_width=True,
    )
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        df_processed.to_excel(writer, index=False, sheet_name="Processado")
    col_xlsx.download_button(
        "⬇️ Baixar Excel",
        data=xlsx_buffer.getvalue(),
        file_name="dataset_processado_pipeline.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
