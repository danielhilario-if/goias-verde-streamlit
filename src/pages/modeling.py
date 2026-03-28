from __future__ import annotations

import pandas as pd
import streamlit as st
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from src.components.dataset_controls import ensure_raw_dataframe, render_dataset_source_toggle
from src.config.settings import MODEL_DEFAULT_FEATURES
from src.ml import DEFAULT_MODEL_KEYS, MODEL_REGISTRY, build_model_pipeline, extract_feature_importance


def render():
    st.subheader("Modelagem")

    df_raw = ensure_raw_dataframe("Carregue um arquivo na aba Upload.")
    if df_raw is None:
        return

    df = render_dataset_source_toggle("model_use_processed")
    if df is None:
        df = df_raw

    numeric_cols = list(df.select_dtypes(include="number").columns)
    all_columns = list(df.columns)

    if len(numeric_cols) < 2:
        st.warning("Sao necessarias colunas numericas suficientes para modelagem.")
        return

    default_target = "FCO2_DRY" if "FCO2_DRY" in all_columns else numeric_cols[0]
    target = st.selectbox("Variavel alvo", options=numeric_cols, index=numeric_cols.index(default_target))

    default_features = [column for column in MODEL_DEFAULT_FEATURES if column in all_columns and column != target]
    features = st.multiselect("Features", options=[column for column in all_columns if column != target], default=default_features)

    if not features:
        st.warning("Selecione ao menos uma feature.")
        return

    selected_models = st.multiselect(
        "Modelos para comparar",
        options=list(MODEL_REGISTRY.keys()),
        default=DEFAULT_MODEL_KEYS,
        format_func=lambda model_key: MODEL_REGISTRY[model_key].label,
    )
    if not selected_models:
        st.warning("Selecione ao menos um modelo para comparação.")
        return

    c1, c2 = st.columns(2)
    test_size = c1.slider("Tamanho do holdout", 0.10, 0.40, 0.30, 0.05)
    cv_folds = c2.slider("Dobras da validacao cruzada", 3, 10, 5, 1)

    df_model = df.dropna(subset=features + [target]).copy()
    if len(df_model) < 30:
        st.warning("Poucos dados apos filtros para treinar modelo (<30 linhas).")
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
    model_details = {}
    failures = []

    for model_key in selected_models:
        model_def = MODEL_REGISTRY[model_key]
        pipeline = build_model_pipeline(model_key, categorical_features, numeric_features)

        try:
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="r2")
        except Exception as exc:
            failures.append(f"{model_def.label}: {exc}")
            continue

        results.append(
            {
                "Modelo": model_def.label,
                "R2 Holdout": r2_score(y_test, predictions),
                "MAE Holdout": mean_absolute_error(y_test, predictions),
                "RMSE Holdout": mean_squared_error(y_test, predictions) ** 0.5,
                "CV R2 media": cv_scores.mean(),
                "CV R2 desvio": cv_scores.std(),
            }
        )

        feature_importance = extract_feature_importance(pipeline)
        if feature_importance is not None and not feature_importance.empty:
            model_details[model_def.label] = feature_importance.head(15)

    if failures:
        for failure in failures:
            st.warning(f"Falha ao treinar modelo: {failure}")

    if not results:
        st.error("Nenhum modelo foi treinado com sucesso.")
        return

    results_df = pd.DataFrame(results).sort_values("CV R2 media", ascending=False)
    st.dataframe(results_df, width="stretch")

    best_model = results_df.iloc[0]
    c1, c2 = st.columns(2)
    c1.metric("Melhor CV R2", f"{best_model['CV R2 media']:.4f}")
    c1.caption(best_model["Modelo"])
    c2.metric("Melhor R2 Holdout", f"{best_model['R2 Holdout']:.4f}")
    c2.caption(best_model["Modelo"])

    if model_details:
        st.markdown("#### Importancias / coeficientes")
        detail_model = st.selectbox("Modelo para inspecionar", options=list(model_details.keys()))
        st.dataframe(model_details[detail_model], width="stretch")
