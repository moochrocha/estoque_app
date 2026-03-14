import streamlit as st
from database.connection import get_connection
from datetime import date

st.title("Entrada de Produtos")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, codigo FROM produtos")
produtos = cursor.fetchall()

lista = {p["codigo"]: p["id"] for p in produtos}

codigo = st.selectbox("Produto", list(lista.keys()))

quantidade = st.number_input("Quantidade adicionada")

data = st.date_input("Data da última reposição", value=date.today())

if st.button("Registrar entrada"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, estoque FROM produtos WHERE codigo = ?", (codigo,))
    produto = cursor.fetchone()

    if produto:

        novo_estoque = produto["estoque"] + quantidade

        cursor.execute("""
        UPDATE produtos
        SET estoque = ?
        WHERE id = ?               
                       """, (novo_estoque, produto["id"]))
        
        cursor.execute("""
        UPDATE produtos
        SET data_reposicao = ?
        WHERE id = ?               
                       """, (data, produto["id"]))
        
        cursor.execute("""
        INSERT INTO movimentacoes
        (produto_id, tipo, quantidade, data)
        VALUES(?, ?, ?, ?)
                       """, (produto["id"], "entrada", quantidade, data))
        
        conn.commit()

        st.success("Estoque atualizado!")

    else:
        st.error("Produto não encontrado")

    conn.close()