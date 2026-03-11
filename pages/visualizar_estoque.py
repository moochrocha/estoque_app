import streamlit as st
import pandas as pd
from database.connection import get_connection

st.title("Estoque de Produtos")

conn = get_connection()

df = pd.read_sql("SELECT id, imagem, codigo, descricao, categoria, estoque, data_reposicao FROM produtos", conn)

# -------
# FILTROS
# -------
st.subheader("Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    busca_descricao = st.text_input("Busca por descrição")

with col2:
    busca_codigo = st.text_input("Busca por código")

with col3:
    categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    filtro_categoria = st.selectbox("Categoria", categorias)

# -------
# APLICAR FILTROS
# -------
df_filtrado = df.copy()

if busca_descricao:
    df_filtrado = df_filtrado[
        df_filtrado["descricao"].str.contains(busca_descricao, case=False)
    ]

if busca_codigo:
    df_filtrado = df_filtrado[
        df_filtrado["codigo"].str.contains(busca_codigo, case=False)
    ]

if filtro_categoria != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["categoria"] == filtro_categoria
    ]

# ---------------
# EXIBIR PRODUTOS
# ---------------
st.subheader(f"Produtos encontrados: {len(df_filtrado)}")

for _, row in df_filtrado.iterrows():

    col1, col2 = st.columns([1, 3])

    with col1:
        if row["imagem"]:
            st.image(f"images/{row['imagem']}", width=100)

    with col2:
        st.write(f"**Código**: {row['codigo']}")
        st.write(f"**Descrição**: {row['descricao']}")
        st.write(f"**Categoria**: {row['categoria']}")
        st.write(f"**Estoque**: {row['estoque']}")
        st.write("---")

conn.close()