from __future__ import annotations

from dataclasses import dataclass

APP_PAGE_TITLE = "Goias Verde - Fluxo do Solo"
APP_LAYOUT = "wide"
APP_SIDEBAR_TITLE = "Projeto Goias Verde"
PRIMARY_COLOR = "#0f766e"
AUTH_VALIDATION_TTL_SECONDS = 300

SESSION_RAW_KEY = "df_raw"
SESSION_PROCESSED_KEY = "df_processed"
SESSION_REPORT_KEY = "df_report"
SESSION_AUTH_ACCESS_TOKEN_KEY = "auth_access_token"
SESSION_AUTH_REFRESH_TOKEN_KEY = "auth_refresh_token"
SESSION_AUTH_USER_KEY = "auth_user"
SESSION_AUTH_VALIDATED_AT_KEY = "auth_validated_at"

SIDEBAR_CSS = """
<style>
section[data-testid="stSidebar"] {
    border-right: 1px solid #e5e7eb;
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}
.ceagre-title {
    font-size: 0.9rem;
    color: #475569;
    margin-top: 0.25rem;
    margin-bottom: 0.8rem;
    text-align: center;
    font-weight: 600;
}
</style>
"""


@dataclass(frozen=True)
class NavigationItem:
    key: str
    label_key: str  # i18n key resolved at render time via src.i18n.t()
    icon: str


NAVIGATION_ITEMS = [
    NavigationItem(key="upload", label_key="nav.upload", icon="cloud-arrow-up"),
    NavigationItem(key="pipeline", label_key="nav.pipeline", icon="sliders"),
    NavigationItem(key="eda", label_key="nav.eda", icon="bar-chart"),
    NavigationItem(key="regression", label_key="nav.regression", icon="graph-up-arrow"),
    NavigationItem(key="modeling", label_key="nav.modeling", icon="cpu"),
    NavigationItem(key="spatial", label_key="nav.spatial", icon="geo-alt"),
    NavigationItem(key="timeseries", label_key="nav.timeseries", icon="activity"),
    NavigationItem(key="comparative", label_key="nav.comparative", icon="diagram-3"),
]

PIPELINE_DROP_CANDIDATES = [
    "Textura",
    "Uso atual",
    "Manejo",
    "CH4_DRY REPLICATE",
    "CO2_DRY REPLICATE",
    "REPLICATE",
    "LABEL",
]
PIPELINE_DIAGNOSTIC_CANDIDATES = ["Diagnostic Initial_value", "DIAGNOSTIC initial_value"]
PIPELINE_R2_CH4_CANDIDATES = ["FCH4_DRY LIN_R2", "FCH4_DRY R2"]
PIPELINE_R2_CO2_CANDIDATES = ["FCO2_DRY R2", "FCO2_DRY LIN_R2"]
PIPELINE_REP_CANDIDATES = ["REP", "Rep"]
PIPELINE_GROUP_CANDIDATES = ["ID", "Fazenda", "Cultura", "Época", "Data", "Date", "Ponto"]

EDA_DEFAULT_DISTRIBUTION_COLUMNS = ["FCO2_DRY", "FCH4_DRY", "TS_2 initial_value", "SWC_2 initial_value"]
EDA_DEFAULT_PAIR_COLUMNS = ["TS_2 initial_value", "SWC_2 initial_value", "FCO2_DRY", "FCH4_DRY"]

REGRESSION_PRESETS = [
    ("Temperatura do Solo x Fluxo de CO2", "TS_2 initial_value", "FCO2_DRY", "Época"),
    ("Umidade do Solo x Fluxo de CO2", "SWC_2 initial_value", "FCO2_DRY", "Época"),
    ("Temperatura do Solo x Fluxo de CH4", "TS_2 initial_value", "FCH4_DRY", "Época"),
]

MODEL_DEFAULT_FEATURES = [
    "Fazenda",
    "Cultura",
    "Época",
    "TS_2 initial_value",
    "SWC_2 initial_value",
    "Latitude",
    "Longitude",
]
