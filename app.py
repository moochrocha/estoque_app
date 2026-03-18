import streamlit as st
import bcrypt
from database.models import create_tables
from services.auth import login_user, logout_user, is_authenticated

st.set_page_config(
    page_title="Gestão de Estoque",
    page_icon="📦",
    layout="wide"
)

create_tables()

# -------------
# TELA DE LOGIN
# -------------
if not is_authenticated():
    st.title("🔐 Acesso ao sistema")
    st.write("Faça login para acessar a aplicação.")

    with st.form("form_login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    if entrar:
        if login_user(username, password):
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.erro("Usuário ou sena inválidos")

    st.stop()

# ----------
# APP LOGADO
# ----------
st.title("📦 Gestão de Estoque Inteligente")
st.write("Aplicação para gerenciamento de estoque.")

with st.sidebar:
    st.success("Selecione uma página")
    st.write(f"Usuário: {st.session_state.get('auth_uuser', '-')}")
    if st.button("Sair", use_container_width=True):
        logout_user()
        st.rerun()