from __future__ import annotations

import seaborn as sns
import streamlit as st

from src.auth import (
    get_authenticated_email,
    get_authenticated_user,
    get_user_role_label,
    is_auth_enabled,
    render_login_gate,
)
from src.components.sidebar import render_sidebar
from src.config.settings import APP_LAYOUT, APP_PAGE_TITLE
from src.pages import PAGE_RENDERERS

st.set_page_config(page_title=APP_PAGE_TITLE, layout=APP_LAYOUT)
sns.set_style("whitegrid")


def main():
    auth_enabled = is_auth_enabled()
    auth_user = get_authenticated_user() if auth_enabled else None

    if auth_enabled and auth_user is None:
        render_login_gate()
        return

    selected_page = render_sidebar(
        user_email=get_authenticated_email(auth_user),
        user_role=get_user_role_label(auth_user) if auth_enabled else None,
        auth_enabled=auth_enabled,
    )
    PAGE_RENDERERS[selected_page]()


if __name__ == "__main__":
    main()
