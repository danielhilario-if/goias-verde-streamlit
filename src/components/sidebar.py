from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

from src.auth import logout
from src.config.settings import APP_SIDEBAR_TITLE, NAVIGATION_ITEMS, PRIMARY_COLOR, SIDEBAR_CSS


def render_sidebar(user_email: str | None = None, user_role: str | None = None, auth_enabled: bool = False) -> str:
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    logo_path = Path(__file__).resolve().parents[2] / "assets" / "logo_CEAGRE.avif"
    if logo_path.exists():
        try:
            st.sidebar.image(str(logo_path), width=200)
        except Exception:
            st.sidebar.caption("Logo CEAGRE encontrado, mas não foi possível renderizar neste ambiente.")

    st.sidebar.markdown(f'<div class="ceagre-title">{APP_SIDEBAR_TITLE}</div>', unsafe_allow_html=True)

    with st.sidebar:
        selected_label = option_menu(
            menu_title=None,
            options=[item.label for item in NAVIGATION_ITEMS],
            icons=[item.icon for item in NAVIGATION_ITEMS],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": PRIMARY_COLOR, "font-size": "18px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "4px 0",
                    "--hover-color": "#e2e8f0",
                    "border-radius": "8px",
                    "padding": "10px 12px",
                },
                "nav-link-selected": {"background-color": PRIMARY_COLOR, "color": "white"},
            },
        )

        if auth_enabled:
            st.markdown("---")
            st.caption(f"Conectado como {user_email or 'usuario'}")
            if user_role:
                st.caption(f"Perfil: {user_role}")
            if st.button("Sair", width="stretch"):
                logout()
                st.rerun()

    return next(item.key for item in NAVIGATION_ITEMS if item.label == selected_label)
