import streamlit as st
import sqlite3
import uuid
import unicodedata
from database.connection import get_connection
from datetime import date
import os

st.set_page_config(
    page_title="Cadastrar produto",
    layout="wide")

st.title("📋 Cadastrar Produto")
# ------------
# FUNÇÕES AUX
# ------------
def normalizar_texto(texto):
    return " ".join(texto.strip().split())

def remover_acentos(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )

# ------
# ESTILO
# ------

st.markdown("""
<style>
/* cartões dos inputs */
div[data-testid="stVerticalBlock"] > div:has(div.stTextInput),
div[data-testid="stVerticalBlock"] > div:has(div.stNumberInput),
div[data-testid="stVerticalBlock"] > div:has(div.stDateInput) {

    border-radius: 15px;
    padding: 20px;
    background-color: rgba(255,255,255,0.02);
}

</style>
""", unsafe_allow_html=True)

# -----
# FORM
# -----

with st.form("form_cadastro_produto"):

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Informações do produto")

        codigo = st.text_input("Código do produto", placeholder="Digite o código")
        descricao = st.text_input("Descrição", placeholder="Descrição do produto")
        categoria = st.text_input("Categoria", placeholder="Categoria do produto")
        fornecedor = st.text_input("Fornecedor", placeholder="Fornecedor do produto")

    with col2:
        st.subheader("Estoque e valores")

        valor_unitario = st.number_input("Valor unitário", min_value=0.0, format="%.2f")
        estoque = st.number_input("Quantidade inicial", min_value=0)
        data = st.date_input("Data da última reposição", value=date.today())

    st.subheader("🖼️ Imagem do produto")    
    imagem = st.file_uploader("Upload da imagem", type=["png", "jpg", "jpeg", "webp"])

    if imagem is not None:
        st.image(imagem, width=250)

    st.markdown("<br>", unsafe_allow_html=True)

    # ------
    # BOTÃO
    # ------
    col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])

    with col_btn2:
        cadastrar = st.form_submit_button("Cadastrar produto", use_container_width=True)

# -------------
# PROCESSAMENTO
# -------------

if cadastrar:

    # padronização
    codigo = normalizar_texto(codigo).upper()
    descricao = normalizar_texto(descricao)
    categoria = remover_acentos(normalizar_texto(categoria)).title()
    fornecedor = remover_acentos(normalizar_texto(fornecedor)).title()

    # validações
    if not codigo:
        st.error("O código do produto é obrigatório.")
        st.stop()

    if not descricao:
        st.error("A descrição do produto é obrigatória.")
        st.stop()

    if not categoria:
        st.error("A categoria do produto é obrigatória.")
        st.stop()

    if not fornecedor:
        st.error("O fornecedor do produto é obrigatório.")
        st.stop()

    os.makedirs("images", exist_ok=True)

    nome_imagem = None

    if imagem is not None:
        extensao = os.path.splitext(imagem.name)[1]
        nome_imagem = f"{uuid.uuid4()}{extensao}"
        caminho = os.path.join("images", nome_imagem)

        with open(caminho, "wb") as f:
            f.write(imagem.getbuffer())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM produtos WHERE codigo = ?", (codigo,))
    existe = cursor.fetchone()

    if existe:
        st.warning("Este código já está cadastrado. ")
        conn.close()
        st.stop()

    try:

        cursor.execute("""
        INSERT INTO produtos (codigo, descricao, categoria, fornecedor, valor_unitario, imagem, estoque, data_reposicao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (codigo, descricao, categoria, fornecedor, valor_unitario, nome_imagem, estoque, data))
        
        conn.commit()
        st.success("✅ Produto cadastrado com sucesso!")
        #st.rerun()

    except sqlite3.IntegrityError:
        st.error("Já existe um produto cadastrado com esse código. Utilize um código diferente.")

    finally:
        conn.close()