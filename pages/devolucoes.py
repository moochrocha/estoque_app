import streamlit as st
import pandas as pd
from database.connection import get_connection
from datetime import date

st.set_page_config(
    page_title="Devoluções",
    layout="wide"
)

st.title("↩️ Devoluções de Produtos")

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

conn.close()

lista = {p["codigo"]: p for p in produtos}

with st.form("registro_devolucao"):

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Produto")

        codigo = st.selectbox(
            "Código produto",
            list(lista.keys())
        )

        produto = lista[codigo]
        produto_id = produto["id"]

        estoque_atual = produto["estoque"]

        st.metric(
            "Estoque atual",
            f"{estoque_atual} unidades"
        )

    with col2:
        st.subheader("📋 Dados da devolução")

        quantidade = st.number_input(
            "Quantidade devolvida",
            min_value=1,
            step=1
        )

        motivo = st.selectbox(
            "Motivo da devolução",
            [
                "Cliente desistiu",
                "Produto com defeito",
                "Produto danificado transporte",
                "Erro no envio",
                "Outro"
            ]
        )

        observacao = st.text_input(
            "Observação (opcional)",
            placeholder="Detalhes adicionais"
        )

        data = st.date_input(
            "Data da devolução",
            value=date.today()
        )

        elegivel = st.toggle(
            "Produto elegível para venda (voltar ao estoque)"
        )

        registrar = st.form_submit_button(
            "Registrar devolução",
            use_container_width=True
        )

# --------
# REGISTRAR
# --------

if registrar:

    conn = get_connection()
    cursor = conn.cursor()

    if observacao:
        motivo_final = f"{motivo} - {observacao}"
    else:
        motivo_final = motivo

    # atualizar estoque se elegível
    if elegivel:

        novo_estoque = estoque_atual + quantidade

        cursor.execute("""
        UPDATE produtos
        SET estoque = ?
        WHERE id = ?
                       """, (novo_estoque, produto_id))
        
    # registrar devolução (sempre)
    cursor.execute("""
    INSERT INTO devolucoes
    (produto_id, quantidade, motivo, elegivel_venda, data)
    VALUES (?, ?, ?, ?, ?)
                    """, (
                        produto_id,
                        quantidade,
                        motivo_final,
                        1 if elegivel else 0,
                        data
                    ))
        
    conn.commit()
    conn.close()

    st.success("✅ Devolução registrada com sucesso!")

    st.rerun()

# ---------
# HISTÓRICO
# ---------

st.divider()

st.subheader("📜 Últimas devoluções")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT d.quantidade, d.motivo, d.elegivel_venda, d.data, p.codigo
FROM devolucoes d
JOIN produtos p ON d.produto_id = p.id
ORDER BY d.data DESC
               """)

devolucoes = cursor.fetchall()

if devolucoes:

    dados = []

    for d in devolucoes:

        status = "✅ Elegível para venda" if d["elegivel_venda"] else "❌ Produto descartado"

        dados.append({
            "Produto": d["codigo"],
            "Quantidade": d["quantidade"],
            "Motivo": d["motivo"],
            "Status": status,
            "Data": d["data"]
        })

    df = pd.DataFrame(dados)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Nenhuma devolução registrada.")