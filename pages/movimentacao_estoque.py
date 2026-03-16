import streamlit as st
import pandas as pd
from database.connection import get_connection
from datetime import date

st.set_page_config(
    page_title="Movimentação Estoque",
    layout="wide"
)

st.title("📦 Movimentação de Estoque")

# ------
# ESTILO
# ------
def colorir_quantidade(val):
    if val.startswith("+"):
        return "color: #16c784; font-weight: bold;"
    else:
        return "color: #ea3943; font-weight: bold;"

st.markdown("""
<style>

/* cartões dos inputs */
div[data-testid="stVerticalBlock"] > div:has(div.stTextInput),
div[data-testid="stVerticalBlock"] > div:has(div.stNumberInput),
div[data-testid="stVerticalBlock"] > div:has(div.stDateInput),
div[data-testid="stVerticalBlock"] > div:has(div[data-baseweb="select"]) {

    
    border-radius: 15px;
    padding: 20px;
    background-color: rgba(255,255,255,0.02);
}

</style>
""", unsafe_allow_html=True)

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, codigo, estoque FROM produtos")
produtos = cursor.fetchall()

lista = {p["codigo"]: p for p in produtos}

with st.form("movimentacao_estoque"):

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Produto")

        codigo = st.selectbox("Código do produto", list(lista.keys()))

        produto = lista[codigo]
        produto_id = produto["id"]

        cursor.execute(
            "SELECT estoque FROM produtos WHERE id = ?",
            (produto_id,)
        )

        estoque_atual = cursor.fetchone()["estoque"]

        st.metric(
            label="Estoque atual",
            value=f"{estoque_atual} unidades"
        )

    with col2:
        st.subheader("📋 Movimentações")

        tipo = st.selectbox("Tipo de movimentação", ["Entrada", "Saída"])

        quantidade = st.number_input("Quantidade", min_value=1)

        data = st.date_input("Data da movimentação", value=date.today())

        motivo = st.selectbox(
            "Motivo da movimentação",
            [
                "Reposição mercadoria",
                "Venda",
                "Produto Quebrado",
                "Ajuste inventário",
                "Outros"
            ]
        )

    observacao = st.text_input(
        "Observação (opcional)",
        placeholder="Detalhes adicionais da movimentação"
    )
        
    registrar = st.form_submit_button(
        "Registrar movimentação",
        use_container_width=True
    )

if registrar:

    cursor.execute(
        "SELECT estoque FROM produtos WHERE id = ?",
        (produto["id"],)
    )

    estoque_atual = cursor.fetchone()["estoque"]

    if tipo == "Entrada":
        novo_estoque = estoque_atual + quantidade
        tipo_db = "entrada"
    else:
        if quantidade > estoque_atual:
            st.error("Quantidade maior que o estoque atual.")
            st.stop()

        novo_estoque = estoque_atual - quantidade
        tipo_db = "saida"

    conn = get_connection()
    cursor = conn.cursor()

    if observacao:
        observacao_final = f"{motivo} - {observacao}"
    else:
        observacao_final = motivo

    cursor.execute("""
    UPDATE produtos
    SET estoque = ?, data_reposicao = ?
    WHERE id = ?
                   """, (novo_estoque, data, produto["id"]))
    
    cursor.execute("""
    INSERT INTO movimentacoes
    (produto_id, tipo, quantidade, data, observacoes)
    VALUES (?, ?, ?, ?, ?)
                   """, (produto["id"], tipo_db, quantidade, data, observacao_final))
    
    conn.commit()
    conn.close()

    st.success("✅ Movimentação registrada com sucesso!")
    st.rerun()

st.divider()

st.subheader("📜 Últimas movimentações")
conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT tipo, quantidade, data, observacoes
FROM movimentacoes
WHERE produto_id = ?
ORDER BY data DESC
LIMIT 10
                """, (produto_id,))

movimentacoes = cursor.fetchall()

if movimentacoes:
    dados = []

    for m in movimentacoes:

        sinal = "+" if m["tipo"] == "entrada" else "-"

        dados.append({
            "Tipo" : m["tipo"].capitalize(),
            "Quantidade" : f"{sinal}{m['quantidade']}",
            "Observação": m["observacoes"],
            "Data": m["data"]
        })

    df = pd.DataFrame(dados)
    
    st.dataframe(
        df.style.map(colorir_quantidade, subset=["Quantidade"]),
        use_container_width=True,
        hide_index=True 
    )
    
else:
    st.info("Nenhuma movimentação registrada para este produto.")

