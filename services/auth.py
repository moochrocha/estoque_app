import hmac
import bcrypt
import streamlit as st

def is_authenticated():
    return st.session_state.get("authenticated", False)


def login_user(username: str, password: str) -> bool:
    expected_username = st.secrets["auth"]["username"]
    password_hash = st.secrets["auth"]["password_hash"].encode()

    username_ok = hmac.compare_digest(username, expected_username)
    password_ok = bcrypt.checkpw(password.encode(), password_hash)

    if username_ok and password_ok:
        st.session_state["authenticated"] = True
        st.session_state["auth_user"] = username
        return True
    
    return False

def logout_user():
    for key in ["authenticated", "auth_user"]:
        if key in st.session_state:
            del st.session_state[key]

def require_login():
    if not is_authenticated():
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()