from __future__ import annotations

import streamlit as st

from src.state import get_excel_sheets, get_raw_dataframe, load_data, set_loaded_dataset


def render():
    st.subheader("Upload de Arquivo")
    uploaded = st.file_uploader("Envie o seu CSV ou Excel", type=["csv", "xlsx", "xls"], key="upload_file")

    if not uploaded:
        st.info("Envie um arquivo para continuar.")
        return

    file_bytes = uploaded.getvalue()
    file_name = uploaded.name

    try:
        sheets = get_excel_sheets(file_bytes, file_name)
    except Exception as exc:
        st.error(f"Nao foi possivel inspecionar o arquivo enviado: {exc}")
        return

    sheet_name = None
    if sheets:
        sheet_name = st.selectbox("Selecione a ABA do Excel", sheets, key="upload_sheet")

    if st.button("Carregar Dataset", type="primary"):
        try:
            df_raw = load_data(file_bytes, file_name, sheet_name)
        except Exception as exc:
            st.error(f"Falha ao carregar o dataset: {exc}")
        else:
            set_loaded_dataset(df_raw)
            st.success(f"Dataset carregado com sucesso: {len(df_raw)} linhas x {len(df_raw.columns)} colunas")

    df_raw = get_raw_dataframe()
    if df_raw is not None:
        c1, c2 = st.columns(2)
        c1.metric("Linhas", len(df_raw))
        c2.metric("Colunas", len(df_raw.columns))
        st.dataframe(df_raw.head(20), width="stretch")
