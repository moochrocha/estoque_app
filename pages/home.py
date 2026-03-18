import streamlit as st
import bcrypt
from database.models import create_tables
from services.auth import require_login, logout_user

require_login()

st.set_page_config(
    page_title="Gestão de Estoque",
    page_icon="📦",
    layout="wide"
)

create_tables()

st.title("📦Gestão de Estoque Inteligente")

st.write("Aplicação para gerenciamento de estoque para e-commerce.")

st.sidebar.success("Selecione uma página")

with st.sidebar:
    if st.button("Sair", use_container_width=True):
        logout_user()
        st.rerun()