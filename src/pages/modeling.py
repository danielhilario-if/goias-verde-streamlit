from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from src.components.dataset_controls import ensure_raw_dataframe, render_dataset_source_toggle
from src.config.settings import MODEL_DEFAULT_FEATURES
from src.i18n import t
from src.ml import DEFAULT_MODEL_KEYS, MODEL_REGISTRY, build_model_pipeline, extract_feature_importance


def render():
    st.subheader(t("modeling.title"))

    df_raw = ensure_raw_dataframe(t("modeling.warn_no_data"))
    if df_raw is None:
        return

    df = render_dataset_source_toggle("model_use_processed")
    if df is None:
        df = df_raw

    numeric_cols = list(df.select_dtypes(include="number").columns)
    all_columns = list(df.columns)

    if len(numeric_cols) < 2:
        st.warning(t("modeling.warn_min_numeric"))
        return

    default_target = "FCO2_DRY" if "FCO2_DRY" in all_columns else numeric_cols[0]
    target = st.selectbox(t("modeling.target"), options=numeric_cols, index=numeric_cols.index(default_target))

    default_features = [column for column in MODEL_DEFAULT_FEATURES if column in all_columns and column != target]
    features = st.multiselect(t("modeling.features"), options=[column for column in all_columns if column != target], default=default_features)

    if not features:
        st.warning(t("modeling.warn_min_feature"))
        return

    selected_models = st.multiselect(
        t("modeling.models"),
        options=list(MODEL_REGISTRY.keys()),
        default=DEFAULT_MODEL_KEYS,
        format_func=lambda model_key: MODEL_REGISTRY[model_key].label,
    )
    if not selected_models:
        st.warning(t("modeling.warn_min_model"))
        return

    c1, c2 = st.columns(2)
    test_size = c1.slider(t("modeling.holdout"), 0.10, 0.40, 0.30, 0.05)
    cv_folds = c2.slider(t("modeling.cv_folds"), 3, 10, 5, 1)

    df_model = df.dropna(subset=features + [target]).copy()
    if len(df_model) < 30:
        st.warning(t("modeling.warn_too_few_rows"))
        return

    X = df_model[features]
    y = df_model[target]

    categorical_features = [
        column for column in features if df_model[column].dtype == "object" or str(df_model[column].dtype).startswith("category")
    ]
    numeric_features = [column for column in features if column not in categorical_features]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

    results = []
    model_details: dict[str, pd.DataFrame] = {}
    holdout_predictions: dict[str, pd.DataFrame] = {}
    failures = []

    for model_key in selected_models:
        model_def = MODEL_REGISTRY[model_key]
        pipeline = build_model_pipeline(model_key, categorical_features, numeric_features)

        try:
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="r2")
        except Exception as exc:
            failures.append(t("modeling.warn_train_failed", error=f"{model_def.label}: {exc}"))
            continue

        results.append(
            {
                t("modeling.col.model"): model_def.label,
                t("modeling.col.r2_holdout"): r2_score(y_test, predictions),
                t("modeling.col.mae_holdout"): mean_absolute_error(y_test, predictions),
                t("modeling.col.rmse_holdout"): mean_squared_error(y_test, predictions) ** 0.5,
                t("modeling.col.cv_mean"): cv_scores.mean(),
                t("modeling.col.cv_std"): cv_scores.std(),
            }
        )

        holdout_predictions[model_def.label] = pd.DataFrame({"observed": y_test.to_numpy(), "predicted": predictions})

        feature_importance = extract_feature_importance(pipeline)
        if feature_importance is not None and not feature_importance.empty:
            model_details[model_def.label] = feature_importance.head(15)

    for failure in failures:
        st.warning(failure)

    if not results:
        st.error(t("modeling.error_no_models"))
        return

    results_df = pd.DataFrame(results).sort_values(t("modeling.col.cv_mean"), ascending=False)
    st.dataframe(results_df, width="stretch")

    best_row = results_df.iloc[0]
    c1, c2 = st.columns(2)
    c1.metric(t("modeling.metric.best_cv"), f"{best_row[t('modeling.col.cv_mean')]:.4f}")
    c1.caption(best_row[t("modeling.col.model")])
    c2.metric(t("modeling.metric.best_holdout"), f"{best_row[t('modeling.col.r2_holdout')]:.4f}")
    c2.caption(best_row[t("modeling.col.model")])

    # ---------------- Predicted vs. observed ----------------
    if holdout_predictions:
        st.markdown(f"#### {t('modeling.predicted_title')}")
        models_for_pred = list(holdout_predictions.keys())
        chosen = st.selectbox(t("modeling.predicted_select"), options=models_for_pred, key="modeling_pred_select")
        pred_df = holdout_predictions[chosen]

        fig_pred, ax_pred = plt.subplots(figsize=(6, 6))
        ax_pred.scatter(pred_df["observed"], pred_df["predicted"], alpha=0.6, s=24, color="#0f766e")
        lim_min = min(pred_df["observed"].min(), pred_df["predicted"].min())
        lim_max = max(pred_df["observed"].max(), pred_df["predicted"].max())
        ax_pred.plot([lim_min, lim_max], [lim_min, lim_max], linestyle="--", color="#b91c1c", linewidth=1.5)
        ax_pred.set_xlabel("observed")
        ax_pred.set_ylabel("predicted")
        ax_pred.set_title(chosen)
        st.pyplot(fig_pred)
        plt.close(fig_pred)
        st.caption(t("modeling.predicted_caption"))

    # ---------------- Feature importance bar chart ----------------
    if model_details:
        st.markdown(f"#### {t('modeling.importance_title')}")
        detail_model = st.selectbox(t("modeling.importance_select"), options=list(model_details.keys()))
        importance_df = model_details[detail_model]
        st.dataframe(importance_df, width="stretch")

        fig_imp, ax_imp = plt.subplots(figsize=(8, max(3, 0.35 * len(importance_df))))
        sns.barplot(
            data=importance_df,
            x="importance",
            y="feature",
            hue="feature",
            legend=False,
            palette="crest",
            ax=ax_imp,
        )
        ax_imp.set_title(t("modeling.importance_chart_title", n=len(importance_df)))
        ax_imp.set_xlabel("importance")
        ax_imp.set_ylabel("")
        st.pyplot(fig_imp)
        plt.close(fig_imp)
