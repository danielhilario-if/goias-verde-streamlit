from __future__ import annotations

import seaborn as sns
import streamlit as st

from src.components.dataset_controls import ensure_raw_dataframe, render_dataset_source_toggle
from src.config.settings import REGRESSION_PRESETS


def render():
    st.subheader("Regressão")

    df_raw = ensure_raw_dataframe("Carregue um arquivo na Aba Upload.")
    if df_raw is None:
        return

    df = render_dataset_source_toggle("reg_use_processed")
    if df is None:
        df = df_raw

    numeric_cols = list(df.select_dtypes(include="number").columns)
    cat_cols = [column for column in df.columns if column not in numeric_cols]
    if len(numeric_cols) < 2:
        st.warning("Sao necessárias ao menos 2 colunas numericas para regressao.")
        return

    st.markdown("#### Presets do notebook")
    preset_labels = [preset[0] for preset in REGRESSION_PRESETS if preset[1] in df.columns and preset[2] in df.columns]
    selected_preset = st.selectbox("Escolha um preset", options=["(nenhum)"] + preset_labels, key="reg_preset")

    if selected_preset != "(nenhum)":
        _, x_p, y_p, hue_p = next(preset for preset in REGRESSION_PRESETS if preset[0] == selected_preset)
        plot_df = df[[x_p, y_p] + ([hue_p] if hue_p in df.columns else [])].dropna().copy()
        if len(plot_df) > 3000:
            plot_df = plot_df.sample(3000, random_state=42)
            st.caption("Amostra de 3000 linhas usada no preset para desempenho.")

        if hue_p in df.columns:
            grid = sns.lmplot(
                data=plot_df,
                x=x_p,
                y=y_p,
                hue=hue_p,
                palette="viridis",
                height=5,
                aspect=1.4,
                scatter_kws={"alpha": 0.5, "s": 20},
                line_kws={"linewidth": 2},
            )
        else:
            grid = sns.lmplot(
                data=plot_df,
                x=x_p,
                y=y_p,
                height=5,
                aspect=1.4,
                scatter_kws={"alpha": 0.5, "s": 20},
                line_kws={"linewidth": 2},
            )
        grid.fig.suptitle(selected_preset, y=1.02)
        st.pyplot(grid.fig)

    st.markdown("#### Regressão customizada")
    default_x = "TS_2 initial_value" if "TS_2 initial_value" in numeric_cols else numeric_cols[0]
    default_y = "FCO2_DRY" if "FCO2_DRY" in numeric_cols else next(column for column in numeric_cols if column != default_x)
    x_var = st.selectbox("Variavel X", options=numeric_cols, index=numeric_cols.index(default_x), key="reg_x")
    y_options = [column for column in numeric_cols if column != x_var]
    y_var = st.selectbox(
        "Variavel Y",
        options=y_options,
        index=y_options.index(default_y) if default_y in y_options else 0,
        key="reg_y",
    )

    hue_options = ["(nenhum)"] + cat_cols
    default_hue = "Época" if "Época" in cat_cols else "(nenhum)"
    hue_var = st.selectbox(
        "Hue (opcional)",
        options=hue_options,
        index=hue_options.index(default_hue),
        key="reg_hue",
    )
    facet_options = ["(nenhum)"] + cat_cols
    facet_var = st.selectbox("Facet por (opcional)", options=facet_options, index=0, key="reg_facet")
    ci_value = st.slider("Intervalo de confianca (%)", 0, 99, 95, 1, key="reg_ci")
    sample_n = st.slider("Amostra maxima para regressao", 100, 5000, 2000, 100, key="reg_sample")

    plot_columns = [x_var, y_var]
    if hue_var != "(nenhum)":
        plot_columns.append(hue_var)
    if facet_var != "(nenhum)" and facet_var not in plot_columns:
        plot_columns.append(facet_var)

    plot_df = df[plot_columns].dropna().copy()
    if len(plot_df) > sample_n:
        plot_df = plot_df.sample(sample_n, random_state=42)
        st.caption(f"Amostra de {sample_n} linhas usada para desempenho.")

    lm_kwargs = {
        "data": plot_df,
        "x": x_var,
        "y": y_var,
        "height": 5,
        "aspect": 1.35,
        "ci": ci_value,
        "scatter_kws": {"alpha": 0.5, "s": 20},
        "line_kws": {"linewidth": 2},
    }
    if hue_var != "(nenhum)":
        lm_kwargs["hue"] = hue_var
        lm_kwargs["palette"] = "magma"
    if facet_var != "(nenhum)":
        lm_kwargs["col"] = facet_var

    grid = sns.lmplot(**lm_kwargs)
    grid.fig.suptitle(f"Regressao: {x_var} x {y_var}", y=1.02)
    st.pyplot(grid.fig)

    corr = plot_df[[x_var, y_var]].corr().iloc[0, 1]
    st.caption(f"Correlação de Pearson ({x_var}, {y_var}): {corr:.4f} | n = {len(plot_df)}")
