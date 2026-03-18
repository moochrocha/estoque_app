import streamlit as st
import time
from datetime import date
from database.connection import get_connection
from services.estoque_service import recalcular_estoque_total, get_estoques_por_produto


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

cursor.execute("SELECT id, codigo, estoque FROM produtos ORDER BY codigo")
produtos = cursor.fetchall()

cursor.execute("SELECT id, nome FROM locais_estoque WHERE ativo = 1 ORDER BY nome")
locais = cursor.fetchall()

conn.close()

# ---------------------
# VALIDAÇÃO SEM PRODUTO
# ---------------------
if not produtos:
    st.warning("Nenhum produto cadastrado no sistema.")
    st.info("Cadastre pelo menos um produto para registrar movimentações de estoque.")
    st.stop()

lista_produtos = {p["codigo"]: p for p in produtos}
lista_locais = {l["nome"]: l["id"] for l in locais}

# ----
# FROM
# ----
with st.form("movimentacao_estoque"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Produto")

        codigo = st.selectbox("Código do produto", list(lista_produtos.keys()))
        produto_id = lista_produtos[codigo]["id"]

        estoques = get_estoques_por_produto(produto_id)
        total = sum(e["quantidade"] for e in estoques)

        st.metric(
            label="Estoque atual",
            value=f"{total} unidades"
        )

        st.write("**Saldo por local:**")
        for e in estoques:
            st.write(f"- {e['local_nome']}: {e['quantidade']}")

    with col2:
        st.subheader("📋 Movimentações")

        tipo = st.selectbox("Tipo de movimentação", ["Entrada", "Saída", "Transferência"])

        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        data_mov = st.date_input("Data da movimentação", value=date.today())

        observacao = st.text_input(
        "Observação",
        placeholder="Detalhes adicionais"
        )
        
        local_origem_nome = None
        local_destino_nome = None

        if tipo == "Entrada":
            local_destino_nome = st.selectbox("Local de destino", list(lista_locais.keys()), key="destino")
        elif tipo == "Saída":
            local_origem_nome = st.selectbox("Local de origem", list(lista_locais.keys()), key="origem")
        else:
            local_origem_nome = st.selectbox("Local de origem", list(lista_locais.keys()), key="origem_transf")
            destinos = [l for l in lista_locais.keys() if l != local_origem_nome]
            local_destino_nome = st.selectbox("Local de destino", destinos, key="destino_transf")

    registrar = st.form_submit_button("Registrar movimentação", use_container_width=True)

    #     motivo = st.selectbox(
    #         "Motivo da movimentação",
    #         [
    #             "Reposição mercadoria",
    #             "Venda",
    #             "Produto Quebrado",
    #             "Ajuste inventário",
    #             "Outros"
    #         ]
    #     )

# ---------------------
# REGISTRAR MOVIMENTAÇÃO
# ---------------------
if registrar:

    conn = get_connection()
    cursor = conn.cursor()

    local_origem_id = lista_locais[local_origem_nome] if local_origem_nome else None
    local_destino_id = lista_locais[local_destino_nome] if local_destino_nome else None
    
    try:

        if tipo == "Entrada":
            cursor.execute("""
                INSERT OR IGNORE INTO estoque_locais (produto_id, local_id, quantidade)
                VALUES (?, ?, 0)
                           """, (produto_id, local_destino_id))

            cursor.execute("""
                UPDATE estoque_locais
                SET quantidade = quantidade + ?
                WHERE produto_id = ? AND local_id = ?
                           """, (quantidade, produto_id, local_destino_id))
            tipo_db = "entrada"
            
        elif tipo == "Saída":
            cursor.execute("""
                SELECT quantidade
                FROM estoque_locais
                WHERE produto_id = ? AND local_id = ?
                           """, (produto_id, local_origem_id))
            
            saldo = cursor.fetchone()
            saldo_atual = saldo["quantidade"] if saldo else 0

            if quantidade > saldo_atual:
                conn.close()
                st.error("Quantidade maior que o estoque disponível no local selecionado.")
                st.stop()

            cursor.execute("""
                UPDATE estoque_locais
                SET quantidade = quantidade - ?
                WHERE produto_id = ? AND local_id = ?
                           """, (quantidade, produto_id, local_origem_id))
            tipo_db = "saida"

        # transfêrencia
        else: 
            cursor.execute("""
                SELECT quantidade
                FROM estoque_locais
                WHERE produto_id = ? AND local_id = ?
                           """, (produto_id, local_origem_id))
            
            saldo = cursor.fetchone()
            saldo_atual = saldo["quantidade"] if saldo else 0

            if quantidade > saldo_atual:
                conn.close()
                st.error("Quantidade maior que o estoque disponível no local de origem.")
                st.stop()

            cursor.execute("""
                INSERT OR IGNORE INTO estoque_locais (produto_id, local_id, quantidade)
                VALUES (?, ?, 0)
                           """, (produto_id, local_destino_id))
            # saída
            cursor.execute("""
                UPDATE estoque_locais
                SET quantidade = quantidade - ?
                WHERE produto_id = ? AND local_id = ?
                           """, (quantidade, produto_id, local_origem_id))
            
            # entrada
            cursor.execute("""
                UPDATE estoque_locais
                SET quantidade = quantidade + ?
                WHERE produto_id = ? AND local_id = ?
                           """, (quantidade, produto_id, local_destino_id))
            
            tipo_db = "transferencia"

        cursor.execute("""
            INSERT INTO movimentacoes
            (produto_id, tipo, quantidade, data, observacoes, local_origem_id, local_destino_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, (
                           produto_id,
                           tipo_db,
                           quantidade,
                           data_mov,
                           observacao if observacao else None,
                           local_origem_id,
                           local_destino_id
                       ))
        
        conn.commit()
        conn.close()

        recalcular_estoque_total(produto_id)

        if tipo_db == "entrada":
            st.success(f"✅ Entrada registrada: +{quantidade} unidades em '{local_destino_nome}'")
            st.toast("Operação concluída", icon="✅")

        elif tipo_db == "saida":
            st.success(f"✅ Saída registrada: -{quantidade} unidades de '{local_origem_nome}'")
            st.toast("Operação concluída", icon="✅")

        elif tipo_db == "transferencia":
            st.success(
                f"🔁 Transferência realizada: {quantidade} unidades de '{local_origem_nome}' → '{local_destino_nome}'"
            )
            st.toast("Operação concluída", icon="✅")

        time.sleep(0.5)
        st.rerun()

    finally:
        try:
            conn.close()
        except:
            pass

#         novo_estoque = estoque_atual - quantidade
#         tipo_db = "saida"

#     if observacao.strip():
#         observacao_final = f"{motivo} - {observacao.strip()}"
#     else:
#         observacao_final = motivo

#     cursor.execute("""
#     UPDATE produtos
#     SET estoque = ?, data_reposicao = ?
#     WHERE id = ?
#                    """, (novo_estoque, data_movimentacao, produto_id))
    
#     cursor.execute("""
#     INSERT INTO movimentacoes
#     (produto_id, tipo, quantidade, data, observacoes)
#     VALUES (?, ?, ?, ?, ?)
#                    """, (produto_id, tipo_db, quantidade, data_movimentacao, observacao_final))
    
#     conn.commit()
#     conn.close()

#     st.success("✅ Movimentação registrada com sucesso!")
#     st.rerun()

# # ---------
# # HISTÓRICO
# # ---------
# st.divider()
# st.subheader("📜 Últimas movimentações")

# conn = get_connection()
# cursor = conn.cursor()

# cursor.execute("""
# SELECT tipo, quantidade, data, observacoes
# FROM movimentacoes
# WHERE produto_id = ?
# ORDER BY data DESC
# LIMIT 10
#                 """, (produto_id,))

# movimentacoes = cursor.fetchall()
# conn.close()

# if movimentacoes:
#     dados = []

#     for m in movimentacoes:

#         sinal = "+" if m["tipo"] == "entrada" else "-"

#         dados.append({
#             "Tipo" : m["tipo"].capitalize(),
#             "Quantidade" : f"{sinal}{m['quantidade']}",
#             "Observação": m["observacoes"],
#             "Data": m["data"]
#         })

#     df = pd.DataFrame(dados)
    
#     st.dataframe(
#         df.style.map(colorir_quantidade, subset=["Quantidade"]),
#         use_container_width=True,
#         hide_index=True 
#     )
    
# else:
#     st.info("Nenhuma movimentação registrada para este produto.")

