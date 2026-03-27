import hmac
import bcrypt
import streamlit as st
import extra_streamlit_components as stx

COOKIE_NAME = "estoque_app_auth"

if "_cookie_manager" not in st.session_state:
    st.session_state["_cookie_manager"] = stx.CookieManager()

cookie_manager = st.session_state["_cookie_manager"]


def is_authenticated():
    if st.session_state.get("authenticated", False):
        return True

    auth_cookie = cookie_manager.get(COOKIE_NAME)
    expected_token = st.secrets["auth"]["cookie_token"]
    expected_username = st.secrets["auth"]["username"]

    if auth_cookie and hmac.compare_digest(auth_cookie, expected_token):
        st.session_state["authenticated"] = True
        st.session_state["auth_user"] = expected_username
        return True

    return False


def login_user(username: str, password: str) -> bool:
    expected_username = st.secrets["auth"]["username"]
    password_hash = st.secrets["auth"]["password_hash"].encode()
    cookie_token = st.secrets["auth"]["cookie_token"]

    username_ok = hmac.compare_digest(username, expected_username)
    password_ok = bcrypt.checkpw(password.encode(), password_hash)

    if username_ok and password_ok:
        st.session_state["authenticated"] = True
        st.session_state["auth_user"] = expected_username

        cookie_manager.set(COOKIE_NAME, cookie_token)
        return True

    return False


def logout_user():
    for key in ["authenticated", "auth_user"]:
        if key in st.session_state:
            del st.session_state[key]

    cookie_manager.delete(COOKIE_NAME)


def require_login():
    if not is_authenticated():
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()


def render_sidebar_logout():
    with st.sidebar:
        if st.button("Sair", use_container_width=True):
            logout_user()
            st.rerun()