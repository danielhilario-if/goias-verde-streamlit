from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src.state import get_active_dataframe, get_raw_dataframe


def ensure_raw_dataframe(warning_message: str) -> Optional[pd.DataFrame]:
    df_raw = get_raw_dataframe()
    if df_raw is None:
        st.warning(warning_message)
    return df_raw


def render_dataset_source_toggle(toggle_key: str, default: bool = True) -> Optional[pd.DataFrame]:
    use_processed = st.toggle("Usar dados processados", value=default, key=toggle_key)
    return get_active_dataframe(use_processed)
