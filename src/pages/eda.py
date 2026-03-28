from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from src.components.dataset_controls import ensure_raw_dataframe, render_dataset_source_toggle
from src.config.settings import EDA_DEFAULT_DISTRIBUTION_COLUMNS, EDA_DEFAULT_PAIR_COLUMNS


def render():
    st.subheader("EDA")

    df_raw = ensure_raw_dataframe("Carregue um arquivo na aba Upload.")
    if df_raw is None:
        return

    df = render_dataset_source_toggle("eda_use_processed")
    if df is None:
        df = df_raw

    all_columns = list(df.columns)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    cat_cols = [column for column in all_columns if column not in numeric_cols]

    if not numeric_cols:
        st.warning("Dataset sem colunas numéricas para EDA.")
        return

    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Resumo Estatístico",
            "Qualidade dos Dados",
            "Relações Bivariadas",
            "Boxplots por Grupo",
            "Dispersão",
            "Correlação",
            "Espacial",
        ]
    )

    with tab0:
        st.markdown("#### Resumo estatístico das variáveis numéricas")
        desc = df[numeric_cols].describe().T
        desc["skewness"] = df[numeric_cols].skew().round(4)
        desc["kurtosis"] = df[numeric_cols].kurt().round(4)
        desc = desc.round(4)
        st.dataframe(desc, width="stretch")
        st.download_button(
            "Baixar resumo estatístico (CSV)",
            data=desc.to_csv(index=True).encode("utf-8-sig"),
            file_name="resumo_estatistico.csv",
            mime="text/csv",
        )

    with tab1:
        st.markdown("#### Qualidade dos dados")
        c1, c2 = st.columns(2)
        c1.metric("Linhas", len(df))
        c2.metric("Colunas", len(df.columns))

        missing_df = (
            df.isna()
            .sum()
            .rename("missing")
            .to_frame()
            .assign(percent=lambda data: (data["missing"] / len(df) * 100).round(2))
            .sort_values("missing", ascending=False)
        )
        st.markdown("##### Missing por coluna")
        st.dataframe(missing_df, width="stretch")

        non_zero_missing = missing_df[missing_df["missing"] > 0]
        if not non_zero_missing.empty:
            fig_missing, ax_missing = plt.subplots(figsize=(10, 4))
            sns.barplot(
                x=non_zero_missing.index,
                y=non_zero_missing["missing"].values,
                hue=non_zero_missing.index,
                legend=False,
                palette="crest",
                ax=ax_missing,
            )
            ax_missing.tick_params(axis="x", rotation=45)
            ax_missing.set_title("Contagem de missing por coluna")
            st.pyplot(fig_missing)
            plt.close(fig_missing)

        if cat_cols:
            st.markdown("##### Frequencia de categorias")
            default_cat = "Época" if "Época" in cat_cols else cat_cols[0]
            cat_col = st.selectbox(
                "Coluna categorica",
                options=cat_cols,
                index=cat_cols.index(default_cat),
                key="eda_quality_cat",
            )
            counts = df[cat_col].value_counts(dropna=False).rename_axis(cat_col).reset_index(name="count")
            st.dataframe(counts, width="stretch")

    with tab2:
        st.markdown("#### Distribuições univariadas")
        default_dist = [column for column in EDA_DEFAULT_DISTRIBUTION_COLUMNS if column in numeric_cols]
        dist_cols = st.multiselect(
            "Selecione variáveis numéricas",
            options=numeric_cols,
            default=default_dist or numeric_cols[:3],
            key="eda_dist_cols",
        )
        bins = st.slider("Numero de bins", 10, 100, 30, key="eda_bins")
        show_kde = st.checkbox("Exibir curva KDE", value=True, key="eda_kde")

        for column in dist_cols:
            fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
            sns.histplot(df[column].dropna(), bins=bins, kde=show_kde, color="#0f766e", ax=ax_hist)
            ax_hist.set_title(f"Distribuicao de {column}")
            st.pyplot(fig_hist)
            plt.close(fig_hist)

    with tab3:
        st.markdown("#### Boxplots por grupo")
        if not cat_cols:
            st.info("Não há colunas categoricas para este bloco.")
        else:
            target = st.selectbox("Variavel alvo (numerica)", options=numeric_cols, key="eda_box_target")
            x_cat = st.selectbox("Agrupar por", options=cat_cols, key="eda_box_x")
            hue_options = ["(nenhum)"] + cat_cols
            hue_col = st.selectbox("Colorir por (Hue é opcional)", options=hue_options, index=0, key="eda_box_hue")

            fig_box, ax_box = plt.subplots(figsize=(10, 5))
            if hue_col != "(nenhum)":
                sns.boxplot(data=df, x=x_cat, y=target, hue=hue_col, palette="Set2", ax=ax_box)
            else:
                sns.boxplot(data=df, x=x_cat, y=target, color="#5fb49c", ax=ax_box)
            ax_box.tick_params(axis="x", rotation=45)
            ax_box.set_title(f"Boxplot: {target} por {x_cat}")
            st.pyplot(fig_box)
            plt.close(fig_box)

    with tab4:
        st.markdown("#### Matriz de dispersão de variáveis")
        default_pair = [column for column in EDA_DEFAULT_PAIR_COLUMNS if column in numeric_cols]
        pair_cols = st.multiselect(
            "Selecione variaveis numericas (2 a 6)",
            options=numeric_cols,
            default=default_pair or numeric_cols[:4],
            key="eda_pair_cols",
        )
        hue_options = ["(nenhum)"] + cat_cols
        hue_col = st.selectbox("Colorir por", options=hue_options, index=0, key="eda_pair_hue")
        sample_n = st.slider("Amostra maxima para plot", 100, 5000, 1200, 100, key="eda_pair_sample")

        if len(pair_cols) < 2:
            st.info("Selecione ao menos 2 variaveis para montar a matriz de dispersao.")
        elif len(pair_cols) > 6:
            st.warning("Selecione no maximo 6 variaveis para manter boa legibilidade.")
        else:
            plot_df = df[pair_cols + ([] if hue_col == "(nenhum)" else [hue_col])].dropna().copy()
            if len(plot_df) > sample_n:
                plot_df = plot_df.sample(sample_n, random_state=42)
                st.caption(f"Pairplot usando amostra de {sample_n} linhas para desempenho.")

            if hue_col == "(nenhum)":
                grid = sns.pairplot(plot_df, vars=pair_cols, corner=True, plot_kws={"alpha": 0.5, "s": 18})
            else:
                grid = sns.pairplot(
                    plot_df,
                    vars=pair_cols,
                    hue=hue_col,
                    corner=True,
                    plot_kws={"alpha": 0.5, "s": 18},
                    palette="viridis",
                )
            grid.fig.suptitle("Matriz de dispersão", y=1.02)
            st.pyplot(grid.fig)

    with tab5:
        st.markdown("#### Matriz de correlação")
        default_corr = numeric_cols[:6] if len(numeric_cols) >= 2 else numeric_cols
        selected_corr = st.multiselect(
            "Selecione variáveis numéricas",
            numeric_cols,
            default=default_corr,
            key="eda_corr_cols",
        )
        if len(selected_corr) >= 2:
            corr_df = df[selected_corr].corr(numeric_only=True)
            fig_corr, ax_corr = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_df, annot=True, cmap="coolwarm", ax=ax_corr)
            st.pyplot(fig_corr)
            st.dataframe(corr_df, width="stretch")
            st.download_button(
                "Baixar correlacao (CSV)",
                data=corr_df.to_csv(index=True).encode("utf-8"),
                file_name="correlacao.csv",
                mime="text/csv",
            )
        else:
            st.info("Selecione ao menos 2 variaveis para calcular correlacao.")

    with tab6:
        st.markdown("#### Análise espacial")
        if "Latitude" not in df.columns or "Longitude" not in df.columns:
            st.info("Colunas Latitude/Longitude nao encontradas.")
        else:
            map_var = st.selectbox("Variavel para cor/tamanho", options=numeric_cols, key="eda_map_var")
            facet_options = ["(nenhum)"] + cat_cols
            facet_col = st.selectbox("Facetar por (opcional)", options=facet_options, key="eda_map_facet")

            if facet_col == "(nenhum)":
                fig_map, ax_map = plt.subplots(figsize=(9, 6))
                sns.scatterplot(
                    data=df,
                    x="Longitude",
                    y="Latitude",
                    hue=map_var,
                    size=map_var,
                    sizes=(20, 180),
                    palette="magma_r",
                    alpha=0.75,
                    ax=ax_map,
                )
                ax_map.set_title(f"Mapa espacial de {map_var}")
                st.pyplot(fig_map)
            else:
                grid = sns.relplot(
                    data=df,
                    x="Longitude",
                    y="Latitude",
                    hue=map_var,
                    size=map_var,
                    sizes=(20, 160),
                    col=facet_col,
                    kind="scatter",
                    palette="magma_r",
                    alpha=0.75,
                    height=4.5,
                    aspect=1,
                )
                grid.figure.suptitle(f"Mapa espacial de {map_var} por {facet_col}", y=1.02)
                st.pyplot(grid.figure)
