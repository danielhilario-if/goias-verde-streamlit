from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st

from src.config.settings import (
    AUTH_VALIDATION_TTL_SECONDS,
    SESSION_AUTH_ACCESS_TOKEN_KEY,
    SESSION_AUTH_REFRESH_TOKEN_KEY,
    SESSION_AUTH_USER_KEY,
    SESSION_AUTH_VALIDATED_AT_KEY,
)

# Margem (em segundos) antes da expiração para tentar renovar o token proativamente.
_TOKEN_REFRESH_MARGIN_SECONDS = 120


@dataclass(frozen=True)
class SupabaseAuthConfig:
    enabled: bool
    url: Optional[str]
    client_key: Optional[str]
    admin_emails: tuple[str, ...]
    allow_signup: bool


def _secret_get(key: str, default: Any = None) -> Any:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _secret_section(name: str) -> dict[str, Any]:
    try:
        if name in st.secrets:
            return dict(st.secrets[name])
    except Exception:
        return {}
    return {}


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_auth_config() -> SupabaseAuthConfig:
    section = _secret_section("supabase")
    url = section.get("url") or _secret_get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    client_key = (
        section.get("publishable_key")
        or section.get("anon_key")
        or _secret_get("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or _secret_get("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    admin_emails_raw = section.get("admin_emails", [])
    admin_emails = tuple(str(email).strip().lower() for email in admin_emails_raw if str(email).strip())
    enabled_value = section.get("enabled")
    enabled = _to_bool(enabled_value) if enabled_value is not None else bool(url and client_key)
    allow_signup_value = section.get("allow_signup")
    allow_signup = _to_bool(allow_signup_value) if allow_signup_value is not None else True
    return SupabaseAuthConfig(enabled=enabled, url=url, client_key=client_key, admin_emails=admin_emails, allow_signup=allow_signup)


def is_auth_enabled() -> bool:
    return get_auth_config().enabled


def _create_supabase_client():
    config = get_auth_config()
    if not config.enabled:
        return None
    if not config.url or not config.client_key:
        raise RuntimeError(
            "Auth habilitada, mas `supabase.url` e `supabase.publishable_key` não foram configurados."
        )
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError("Dependência `supabase` não instalada. Rode `pip install -r requirements.txt`.") from exc

    return create_client(config.url, config.client_key)


def _serialize_user(user: Any) -> dict[str, Any]:
    if user is None:
        return {}
    if isinstance(user, dict):
        return user
    if hasattr(user, "model_dump"):
        return user.model_dump()
    if hasattr(user, "dict"):
        return user.dict()

    serialized = {}
    for field in ("id", "email", "role", "aud", "app_metadata", "user_metadata"):
        value = getattr(user, field, None)
        if value is not None:
            serialized[field] = value
    return serialized


def _store_auth_session(response: Any) -> dict[str, Any]:
    session = getattr(response, "session", None)
    user = getattr(response, "user", None) or getattr(session, "user", None)
    access_token = getattr(session, "access_token", None)
    refresh_token = getattr(session, "refresh_token", None)

    if not access_token or user is None:
        raise RuntimeError("Supabase não retornou uma sessão ativa. Verifique suas credenciais e se o e-mail foi confirmado.")

    user_data = _serialize_user(user)
    st.session_state[SESSION_AUTH_ACCESS_TOKEN_KEY] = access_token
    st.session_state[SESSION_AUTH_REFRESH_TOKEN_KEY] = refresh_token
    st.session_state[SESSION_AUTH_USER_KEY] = user_data
    st.session_state[SESSION_AUTH_VALIDATED_AT_KEY] = time.time()
    return user_data


def clear_auth_state():
    for key in (
        SESSION_AUTH_ACCESS_TOKEN_KEY,
        SESSION_AUTH_REFRESH_TOKEN_KEY,
        SESSION_AUTH_USER_KEY,
        SESSION_AUTH_VALIDATED_AT_KEY,
    ):
        st.session_state.pop(key, None)


def _try_refresh_token() -> Optional[dict[str, Any]]:
    """Tenta renovar a sessão usando o refresh_token armazenado.

    Retorna os dados do usuário atualizados em caso de sucesso, ou None se falhar.
    O estado de sessão é limpo em caso de falha definitiva.
    """
    refresh_token = st.session_state.get(SESSION_AUTH_REFRESH_TOKEN_KEY)
    if not refresh_token:
        clear_auth_state()
        return None

    try:
        client = _create_supabase_client()
        response = client.auth.refresh_session(refresh_token)
        return _store_auth_session(response)
    except Exception:
        clear_auth_state()
        return None


def sign_in_with_password(email: str, password: str) -> dict[str, Any]:
    """Autentica o usuário com e-mail e senha.

    Raises:
        RuntimeError: se as credenciais forem inválidas, e-mail não confirmado,
                      ou qualquer falha de rede/configuração.
    """
    if not email or not password:
        raise RuntimeError("Preencha e-mail e senha antes de continuar.")

    client = _create_supabase_client()
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        msg = str(exc).lower()
        if "invalid login credentials" in msg or "invalid_credentials" in msg:
            raise RuntimeError("E-mail ou senha incorretos. Verifique os dados e tente novamente.") from exc
        if "email not confirmed" in msg:
            raise RuntimeError("E-mail ainda não confirmado. Verifique sua caixa de entrada.") from exc
        if "rate limit" in msg or "too many requests" in msg:
            raise RuntimeError("Muitas tentativas de login. Aguarde alguns minutos e tente novamente.") from exc
        raise RuntimeError(f"Falha na autenticação: {exc}") from exc

    return _store_auth_session(response)


def sign_up_with_password(email: str, password: str) -> bool:
    """Cadastra um novo usuário com e-mail e senha.

    Retorna True se o cadastro foi realizado e confirmação de e-mail foi enviada,
    ou False se o usuário já existia (sem revelar isso explicitamente ao cliente).

    Raises:
        RuntimeError: em caso de senha fraca, e-mail inválido ou erro de rede.
    """
    if not email or not password:
        raise RuntimeError("Preencha e-mail e senha antes de continuar.")
    if len(password) < 6:
        raise RuntimeError("A senha deve ter ao menos 6 caracteres.")

    client = _create_supabase_client()
    try:
        client.auth.sign_up({"email": email, "password": password})
        return True
    except Exception as exc:
        msg = str(exc).lower()
        if "password" in msg and ("weak" in msg or "short" in msg):
            raise RuntimeError("Senha muito fraca. Use ao menos 6 caracteres com letras e números.") from exc
        if "rate limit" in msg or "too many requests" in msg:
            raise RuntimeError("Muitas tentativas. Aguarde alguns minutos e tente novamente.") from exc
        if "invalid email" in msg:
            raise RuntimeError("Endereço de e-mail inválido.") from exc
        raise RuntimeError(f"Erro ao cadastrar: {exc}") from exc


def get_authenticated_user() -> Optional[dict[str, Any]]:
    """Retorna o usuário autenticado da sessão atual.

    Fluxo:
      1. Se o token ainda está dentro do TTL de validação → retorna cache.
      2. Se o token está próximo da expiração (< _TOKEN_REFRESH_MARGIN_SECONDS)
         ou expirou o TTL → tenta renovar via refresh_token.
      3. Se a renovação falhar → limpa estado e retorna None.
    """
    if not is_auth_enabled():
        return None

    access_token = st.session_state.get(SESSION_AUTH_ACCESS_TOKEN_KEY)
    cached_user = st.session_state.get(SESSION_AUTH_USER_KEY)
    validated_at = st.session_state.get(SESSION_AUTH_VALIDATED_AT_KEY, 0.0)

    if not access_token:
        return None

    elapsed = time.time() - validated_at

    # Dentro do TTL: retorna cache sem nenhuma chamada de rede.
    if cached_user and elapsed < AUTH_VALIDATION_TTL_SECONDS:
        return cached_user

    # Fora do TTL: revalida o token com o Supabase.
    # Se o token estiver próximo de expirar, preferimos fazer refresh logo.
    try:
        client = _create_supabase_client()
        response = client.auth.get_user(access_token)
    except Exception:
        # Token inválido ou expirado: tenta renovar com o refresh_token.
        return _try_refresh_token()

    user = getattr(response, "user", None)
    if user is None:
        return _try_refresh_token()

    user_data = _serialize_user(user)
    st.session_state[SESSION_AUTH_USER_KEY] = user_data
    st.session_state[SESSION_AUTH_VALIDATED_AT_KEY] = time.time()
    return user_data


def get_authenticated_email(user: Optional[dict[str, Any]]) -> Optional[str]:
    if not user:
        return None
    return user.get("email")


def is_admin_user(user: Optional[dict[str, Any]]) -> bool:
    email = get_authenticated_email(user)
    if not email:
        return False
    return email.strip().lower() in get_auth_config().admin_emails


def get_user_role_label(user: Optional[dict[str, Any]]) -> str:
    return "Administrador" if is_admin_user(user) else "Usuário"


def logout():
    """Encerra a sessão local. Não invalida o token no servidor Supabase."""
    clear_auth_state()


def render_login_gate():
    config = get_auth_config()

    st.title("Projeto Goiás Verde")
    st.caption("Faça login para acessar o produto Streamlit.")

    if not config.url or not config.client_key:
        st.error("A autenticação Supabase foi habilitada, mas as credenciais não foram configuradas.")
        st.info("Adicione as credenciais em `.streamlit/secrets.toml` conforme o exemplo `.streamlit/secrets.toml.example`.")
        st.code(
            "[supabase]\n"
            "enabled = true\n"
            'url = "https://SEU-PROJETO.supabase.co"\n'
            'publishable_key = "SUA_CHAVE_PUBLISHABLE"\n'
            'admin_emails = ["admin@dominio.com"]\n'
        )
        return

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        tab_labels = ["Entrar", "Cadastrar"] if config.allow_signup else ["Entrar"]
        tabs = st.tabs(tab_labels)

        # --- Aba: Entrar ---
        with tabs[0]:
            with st.form("supabase_login_form", clear_on_submit=False):
                email_login = st.text_input("E-mail", key="login_email")
                password_login = st.text_input("Senha", type="password", key="login_password")
                submitted_login = st.form_submit_button("Entrar", type="primary", width="stretch")

            if submitted_login:
                try:
                    sign_in_with_password(email=email_login, password=password_login)
                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Erro inesperado: {exc}")
                else:
                    st.success("Login realizado com sucesso.")
                    st.rerun()

        # --- Aba: Cadastrar ---
        if config.allow_signup:
            with tabs[1]:
                st.caption("Crie sua conta. Após o cadastro, um e-mail de confirmação será enviado.")
                with st.form("supabase_signup_form", clear_on_submit=True):
                    email_signup = st.text_input("E-mail", key="signup_email")
                    password_signup = st.text_input(
                        "Senha", type="password", key="signup_password",
                        help="Mínimo 6 caracteres.",
                    )
                    password_confirm = st.text_input("Confirme a senha", type="password", key="signup_password_confirm")
                    submitted_signup = st.form_submit_button("Criar conta", type="primary", width="stretch")

                if submitted_signup:
                    if password_signup != password_confirm:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            sign_up_with_password(email=email_signup, password=password_signup)
                        except RuntimeError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            st.error(f"Erro inesperado: {exc}")
                        else:
                            st.success("Conta criada! Verifique sua caixa de entrada para confirmar o e-mail antes de fazer login.")
