import streamlit as st
from database.models import create_tables

create_tables()

st.set_page_config(
    page_title="Gestão de Estoque",
    page_icon="📦",
    layout="wide"
)

st.title("📦Gestão de Estoque Inteligente")

st.write("Aplicação para gerenciamento de estoque para e-commerce.")

st.sidebar.success("Selecione uma página")