from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor


@dataclass(frozen=True)
class ModelDefinition:
    key: str
    label: str
    scale_numeric: bool
    estimator_factory: Callable[[], Any]


MODEL_REGISTRY = {
    "linear_regression": ModelDefinition(
        key="linear_regression",
        label="Linear Regression",
        scale_numeric=True,
        estimator_factory=lambda: LinearRegression(),
    ),
    "random_forest": ModelDefinition(
        key="random_forest",
        label="Random Forest",
        scale_numeric=False,
        estimator_factory=lambda: RandomForestRegressor(n_estimators=200, random_state=42),
    ),
    "decision_tree": ModelDefinition(
        key="decision_tree",
        label="Decision Tree",
        scale_numeric=False,
        estimator_factory=lambda: DecisionTreeRegressor(random_state=42),
    ),
    "gradient_boosting": ModelDefinition(
        key="gradient_boosting",
        label="Gradient Boosting",
        scale_numeric=False,
        estimator_factory=lambda: GradientBoostingRegressor(random_state=42),
    ),
    "knn": ModelDefinition(
        key="knn",
        label="K-Nearest Neighbors",
        scale_numeric=True,
        estimator_factory=lambda: KNeighborsRegressor(n_neighbors=5),
    ),
}

DEFAULT_MODEL_KEYS = ["linear_regression", "random_forest"]


def build_model_pipeline(model_key: str, categorical_features: list[str], numeric_features: list[str]) -> Pipeline:
    model_def = MODEL_REGISTRY[model_key]
    numeric_transformer = StandardScaler() if model_def.scale_numeric else "passthrough"

    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("num", numeric_transformer, numeric_features),
        ]
    )

    return Pipeline(steps=[("preprocess", preprocess), ("model", model_def.estimator_factory())])


def extract_feature_importance(model_pipeline: Pipeline) -> pd.DataFrame | None:
    preprocess = model_pipeline.named_steps["preprocess"]
    estimator = model_pipeline.named_steps["model"]
    feature_names = preprocess.get_feature_names_out()

    if hasattr(estimator, "feature_importances_"):
        importance_values = np.asarray(estimator.feature_importances_)
    elif hasattr(estimator, "coef_"):
        importance_values = np.abs(np.ravel(estimator.coef_))
    else:
        return None

    if len(feature_names) != len(importance_values):
        return None

    return pd.DataFrame({"feature": feature_names, "importance": importance_values}).sort_values(
        "importance", ascending=False
    )
