from __future__ import annotations

import streamlit as st

from src.i18n import t
from src.state import get_excel_sheets, get_raw_dataframe, load_data, set_loaded_dataset


def render():
    st.subheader(t("upload.title"))
    uploaded = st.file_uploader(t("upload.uploader_label"), type=["csv", "xlsx", "xls"], key="upload_file")

    if not uploaded:
        st.info(t("upload.info_send_file"))
        return

    file_bytes = uploaded.getvalue()
    file_name = uploaded.name

    try:
        sheets = get_excel_sheets(file_bytes, file_name)
    except Exception as exc:
        st.error(t("upload.error_inspect", error=exc))
        return

    sheet_name = None
    if sheets:
        sheet_name = st.selectbox(t("upload.select_sheet"), sheets, key="upload_sheet")

    if st.button(t("upload.load_button"), type="primary"):
        try:
            df_raw = load_data(file_bytes, file_name, sheet_name)
        except Exception as exc:
            st.error(t("upload.error_load", error=exc))
        else:
            set_loaded_dataset(df_raw)
            st.success(t("upload.success_loaded", rows=len(df_raw), cols=len(df_raw.columns)))

    df_raw = get_raw_dataframe()
    if df_raw is not None:
        c1, c2 = st.columns(2)
        c1.metric(t("upload.metric_rows"), len(df_raw))
        c2.metric(t("upload.metric_cols"), len(df_raw.columns))
        st.dataframe(df_raw.head(20), width="stretch")
