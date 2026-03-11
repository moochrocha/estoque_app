import streamlit as st
from database.connection import get_connection
from datetime import date
import os

st.title("Cadastrar Produto")

codigo = st.text_input("Código do produto")
descricao = st.text_input("Descrição")
categoria = st.text_input("Categoria")
estoque = st.number_input("Quantidade inicial", min_value=0)
data = st.date_input("Data da última reposição", value=date.today())
imagem = st.file_uploader("Imagem do produto")

if st.button("Cadastrar produto"):

    nome_imagem = None

    if imagem is not None:

        nome_imagem = imagem.name

        caminho = os.path.join("images", nome_imagem)

        with open(caminho, "wb") as f:
            f.write(imagem.getbuffer())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO produtos (codigo, descricao, categoria, imagem, estoque, data_reposicao)
    VALUES (?, ?, ?, ?, ?, ?)
                   """, (codigo, descricao, categoria, nome_imagem, estoque, data))
    
    conn.commit()
    conn.close()

    st.success("Produto cadastrado com sucesso!")