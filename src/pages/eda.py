from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.components.dataset_controls import ensure_raw_dataframe, render_dataset_source_toggle
from src.config.settings import EDA_DEFAULT_DISTRIBUTION_COLUMNS, EDA_DEFAULT_PAIR_COLUMNS
from src.i18n import t

_DATE_CANDIDATES = ("Data", "Date", "DATE", "data", "date")


def _find_date_column(df: pd.DataFrame) -> str | None:
    for candidate in _DATE_CANDIDATES:
        if candidate in df.columns:
            return candidate
    return None


def render():
    st.subheader(t("eda.title"))

    df_raw = ensure_raw_dataframe(t("eda.warn_no_data"))
    if df_raw is None:
        return

    df = render_dataset_source_toggle("eda_use_processed")
    if df is None:
        df = df_raw

    all_columns = list(df.columns)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    cat_cols = [column for column in all_columns if column not in numeric_cols]

    if not numeric_cols:
        st.warning(t("eda.warn_no_numeric"))
        return

    none_label = t("common.none")

    tabs = st.tabs(
        [
            t("eda.tab.summary"),
            t("eda.tab.quality"),
            t("eda.tab.bivariate"),
            t("eda.tab.boxplots"),
            t("eda.tab.scatter"),
            t("eda.tab.correlation"),
            t("eda.tab.spatial"),
            t("eda.tab.temporal"),
            t("eda.tab.composition"),
        ]
    )
    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs

    # ---------------- Tab 0: summary ----------------
    with tab0:
        st.markdown(f"#### {t('eda.summary.title')}")
        desc = df[numeric_cols].describe().T
        desc["skewness"] = df[numeric_cols].skew().round(4)
        desc["kurtosis"] = df[numeric_cols].kurt().round(4)
        desc = desc.round(4)
        st.dataframe(desc, width="stretch")
        st.download_button(
            t("eda.summary.download"),
            data=desc.to_csv(index=True).encode("utf-8-sig"),
            file_name="resumo_estatistico.csv",
            mime="text/csv",
        )

    # ---------------- Tab 1: data quality ----------------
    with tab1:
        st.markdown(f"#### {t('eda.quality.title')}")
        c1, c2 = st.columns(2)
        c1.metric(t("eda.quality.metric_rows"), len(df))
        c2.metric(t("eda.quality.metric_cols"), len(df.columns))

        missing_df = (
            df.isna()
            .sum()
            .rename("missing")
            .to_frame()
            .assign(percent=lambda data: (data["missing"] / len(df) * 100).round(2))
            .sort_values("missing", ascending=False)
        )
        st.markdown(f"##### {t('eda.quality.missing_title')}")
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
            ax_missing.set_title(t("eda.quality.missing_chart_title"))
            st.pyplot(fig_missing)
            plt.close(fig_missing)

        if cat_cols:
            st.markdown(f"##### {t('eda.quality.cat_title')}")
            default_cat = "Época" if "Época" in cat_cols else cat_cols[0]
            cat_col = st.selectbox(
                t("eda.quality.cat_select"),
                options=cat_cols,
                index=cat_cols.index(default_cat),
                key="eda_quality_cat",
            )
            counts = df[cat_col].value_counts(dropna=False).rename_axis(cat_col).reset_index(name="count")
            st.dataframe(counts, width="stretch")

    # ---------------- Tab 2: bivariate (univariate distributions) ----------------
    with tab2:
        st.markdown(f"#### {t('eda.bivariate.title')}")
        default_dist = [column for column in EDA_DEFAULT_DISTRIBUTION_COLUMNS if column in numeric_cols]
        dist_cols = st.multiselect(
            t("eda.bivariate.select"),
            options=numeric_cols,
            default=default_dist or numeric_cols[:3],
            key="eda_dist_cols",
        )
        bins = st.slider(t("eda.bivariate.bins"), 10, 100, 30, key="eda_bins")
        show_kde = st.checkbox(t("eda.bivariate.kde"), value=True, key="eda_kde")

        for column in dist_cols:
            fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
            sns.histplot(df[column].dropna(), bins=bins, kde=show_kde, color="#0f766e", ax=ax_hist)
            ax_hist.set_title(t("eda.bivariate.dist_title", col=column))
            st.pyplot(fig_hist)
            plt.close(fig_hist)

    # ---------------- Tab 3: boxplots / violin ----------------
    with tab3:
        st.markdown(f"#### {t('eda.boxplot.title')}")
        if not cat_cols:
            st.info(t("eda.boxplot.no_cat"))
        else:
            target = st.selectbox(t("eda.boxplot.target"), options=numeric_cols, key="eda_box_target")
            x_cat = st.selectbox(t("eda.boxplot.x"), options=cat_cols, key="eda_box_x")
            hue_options = [none_label] + cat_cols
            hue_col = st.selectbox(t("eda.boxplot.hue"), options=hue_options, index=0, key="eda_box_hue")
            kind_label = st.radio(
                t("eda.boxplot.kind"),
                options=[t("eda.boxplot.kind.box"), t("eda.boxplot.kind.violin")],
                horizontal=True,
                key="eda_box_kind",
            )

            fig_box, ax_box = plt.subplots(figsize=(10, 5))
            plot_func = sns.boxplot if kind_label == t("eda.boxplot.kind.box") else sns.violinplot
            if hue_col != none_label:
                plot_func(data=df, x=x_cat, y=target, hue=hue_col, palette="Set2", ax=ax_box)
            else:
                plot_func(data=df, x=x_cat, y=target, color="#5fb49c", ax=ax_box)
            ax_box.tick_params(axis="x", rotation=45)
            ax_box.set_title(t("eda.boxplot.title_dynamic", target=target, x=x_cat))
            st.pyplot(fig_box)
            plt.close(fig_box)

    # ---------------- Tab 4: scatter / pairplot ----------------
    with tab4:
        st.markdown(f"#### {t('eda.scatter.title')}")
        default_pair = [column for column in EDA_DEFAULT_PAIR_COLUMNS if column in numeric_cols]
        pair_cols = st.multiselect(
            t("eda.scatter.select"),
            options=numeric_cols,
            default=default_pair or numeric_cols[:4],
            key="eda_pair_cols",
        )
        hue_options = [none_label] + cat_cols
        hue_col = st.selectbox(t("eda.scatter.hue"), options=hue_options, index=0, key="eda_pair_hue")
        sample_n = st.slider(t("eda.scatter.sample"), 100, 5000, 1200, 100, key="eda_pair_sample")

        if len(pair_cols) < 2:
            st.info(t("eda.scatter.info_min"))
        elif len(pair_cols) > 6:
            st.warning(t("eda.scatter.warn_max"))
        else:
            plot_df = df[pair_cols + ([] if hue_col == none_label else [hue_col])].dropna().copy()
            if len(plot_df) > sample_n:
                plot_df = plot_df.sample(sample_n, random_state=42)
                st.caption(t("eda.scatter.caption_sample", n=sample_n))

            if hue_col == none_label:
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
            grid.fig.suptitle(t("eda.scatter.title_dynamic"), y=1.02)
            st.pyplot(grid.fig)

    # ---------------- Tab 5: correlation ----------------
    with tab5:
        st.markdown(f"#### {t('eda.corr.title')}")
        default_corr = numeric_cols[:6] if len(numeric_cols) >= 2 else numeric_cols
        selected_corr = st.multiselect(
            t("eda.corr.select"),
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
                t("eda.corr.download"),
                data=corr_df.to_csv(index=True).encode("utf-8"),
                file_name="correlacao.csv",
                mime="text/csv",
            )
        else:
            st.info(t("eda.corr.info_min"))

    # ---------------- Tab 6: spatial ----------------
    with tab6:
        st.markdown(f"#### {t('eda.spatial.title')}")
        if "Latitude" not in df.columns or "Longitude" not in df.columns:
            st.info(t("eda.spatial.no_coords"))
        else:
            map_var = st.selectbox(t("eda.spatial.var"), options=numeric_cols, key="eda_map_var")
            facet_options = [none_label] + cat_cols
            facet_col = st.selectbox(t("eda.spatial.facet"), options=facet_options, key="eda_map_facet")

            if facet_col == none_label:
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
                ax_map.set_title(t("eda.spatial.title_dynamic", var=map_var))
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
                grid.figure.suptitle(t("eda.spatial.title_facet", var=map_var, facet=facet_col), y=1.02)
                st.pyplot(grid.figure)

    # ---------------- Tab 7: temporal (NEW) ----------------
    with tab7:
        st.markdown(f"#### {t('eda.temporal.title')}")
        date_col = _find_date_column(df)
        if date_col is None:
            st.info(t("eda.temporal.no_date"))
        else:
            default_var = "FCO2_DRY" if "FCO2_DRY" in numeric_cols else numeric_cols[0]
            var = st.selectbox(
                t("eda.temporal.var"),
                options=numeric_cols,
                index=numeric_cols.index(default_var),
                key="eda_temporal_var",
            )
            hue_options = [none_label] + cat_cols
            default_hue = "Cultura" if "Cultura" in cat_cols else none_label
            hue_col = st.selectbox(
                t("eda.temporal.hue"),
                options=hue_options,
                index=hue_options.index(default_hue),
                key="eda_temporal_hue",
            )
            agg_label = st.radio(
                t("eda.temporal.aggregate"),
                options=[t("eda.temporal.aggregate.mean"), t("eda.temporal.aggregate.median")],
                horizontal=True,
                key="eda_temporal_agg",
            )
            agg_func = "mean" if agg_label == t("eda.temporal.aggregate.mean") else "median"

            work = df[[date_col, var] + ([hue_col] if hue_col != none_label else [])].dropna().copy()
            work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
            work = work.dropna(subset=[date_col])
            if not work.empty:
                group_cols = [date_col] + ([hue_col] if hue_col != none_label else [])
                series = work.groupby(group_cols, as_index=False)[var].agg(agg_func)

                fig_ts, ax_ts = plt.subplots(figsize=(10, 4.5))
                if hue_col == none_label:
                    sns.lineplot(data=series, x=date_col, y=var, marker="o", color="#0f766e", ax=ax_ts)
                else:
                    sns.lineplot(data=series, x=date_col, y=var, hue=hue_col, marker="o", palette="viridis", ax=ax_ts)
                ax_ts.set_title(t("eda.temporal.title_dynamic", var=var))
                ax_ts.tick_params(axis="x", rotation=30)
                st.pyplot(fig_ts)
                plt.close(fig_ts)

    # ---------------- Tab 8: composition (NEW) ----------------
    with tab8:
        st.markdown(f"#### {t('eda.composition.title')}")
        if not cat_cols:
            st.info(t("eda.composition.no_cat"))
        else:
            default_cat = "Cultura" if "Cultura" in cat_cols else cat_cols[0]
            comp_col = st.selectbox(
                t("eda.composition.col"),
                options=cat_cols,
                index=cat_cols.index(default_cat),
                key="eda_composition_col",
            )
            counts = df[comp_col].value_counts(dropna=False)
            fig_comp, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(12, 5))
            sns.barplot(
                x=counts.index.astype(str),
                y=counts.values,
                hue=counts.index.astype(str),
                legend=False,
                palette="viridis",
                ax=ax_bar,
            )
            ax_bar.tick_params(axis="x", rotation=30)
            ax_bar.set_title(t("eda.composition.title_dynamic", col=comp_col))
            ax_pie.pie(counts.values, labels=counts.index.astype(str), autopct="%1.1f%%", colors=sns.color_palette("viridis", len(counts)))
            ax_pie.set_title(t("eda.composition.title_dynamic", col=comp_col))
            st.pyplot(fig_comp)
            plt.close(fig_comp)
