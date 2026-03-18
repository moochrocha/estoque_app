import streamlit as st
from database.connection import get_connection
from datetime import date, datetime

st.set_page_config(
    page_title="Devoluções",
    page_icon="↩️",
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

# -----------
# FUNÇÕES AUX
# -----------
def normalizar_texto(texto):
    return " ".join(texto.strip().split())

if "devolucao_editar_id" not in st.session_state:
    st.session_state["devolucao_editar_id"] = None

if "devolucao_excluir_id" not in st.session_state:
    st.session_state["devolucao_excluir_id"] = None
# -----------------
# CARREGAR PRODUTOS
# -----------------
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, codigo, estoque FROM produtos")
produtos = cursor.fetchall()

conn.close()

lista = {p["codigo"]: p for p in produtos}

# ----
# FORM
# ----
if not lista:
    st.warning("Nenhum produto cadastrado. Cadastre produtos antes de registrar devoluções.")
else:
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
                    "Produto danificado no transporte",
                    "Erro no envio",
                    "Outro"
                ]
            )

            observacao = st.text_input(
                "Observação (opcional)",
                placeholder="Detalhes adicionais"
            )

            plataforma = st.selectbox(
                "Plataforma",
                [
                    "Shopee",
                    "Mercado Livre",
                    "Amazon",
                    "Magalu",
                    "Tik Tok Shop",
                    "Outro"
                ]
            )

            id_solicitacao = st.text_input(
                "ID da solicitação (opcional)",
                placeholder="25121000B8KHVC1"
            )

            link_solicitacao = st.text_input(
                "Link da solicitação (opcional)",
                placeholder="https://..."
            )

            data_devolucao = st.date_input(
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

        # padronizar
        observacao = normalizar_texto(observacao)
        id_solicitacao = normalizar_texto(id_solicitacao).upper()
        link_solicitacao = normalizar_texto(link_solicitacao)

        if link_solicitacao and not (
            link_solicitacao.startswith("http://") or link_solicitacao.startswith("https://")
        ):
            st.error("O link da solicitaçao deve começar com http:// ou https://")
            st.stop()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # atualizar estoque se elegível
            if elegivel:

                novo_estoque = estoque_atual + quantidade

                cursor.execute("""
                UPDATE produtos
                SET estoque = ?
                WHERE id = ?
                            """, (novo_estoque, produto_id))
                
            # registrar devolução
            cursor.execute("""
            INSERT INTO devolucoes  (
                        produto_id,
                        quantidade,
                        motivo,
                        observacoes,
                        plataforma,
                        id_solicitacao,
                        link_solicitacao,
                        elegivel_venda,
                        data
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                produto_id,
                quantidade,
                motivo,
                observacao if observacao else None,
                plataforma,
                id_solicitacao if id_solicitacao else None,
                link_solicitacao if link_solicitacao else None,
                1 if elegivel else 0,
                data_devolucao
            ))
                
            conn.commit()
            st.success("✅ Devolução registrada com sucesso!")
            st.rerun()

        finally:
            conn.close()

# ---------
# HISTÓRICO
# ---------

st.divider()

st.subheader("📜 Últimas devoluções")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
SELECT
    d.id,
    d.quantidade, 
    d.motivo,
    d.observacoes,
    d.plataforma,
    d.id_solicitacao,
    d.link_solicitacao,
    d.elegivel_venda, 
    d.data,
    p.codigo
FROM devolucoes d
JOIN produtos p ON d.produto_id = p.id
ORDER BY d.data DESC, d.id DESC
""")

devolucoes = cursor.fetchall()
conn.close()

if devolucoes:
    for d in devolucoes:

        status = "✅ Elegível para venda" if d["elegivel_venda"] else "❌ Produto descartado"
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**Produto:** {d['codigo']}")
                st.write(f"**Quantidade:** {d['quantidade']}")
                st.write(f"**Motivo:** {d['motivo']}")
                st.write(f"**Observações:** {d['observacoes'] if d['observacoes'] else '-'}")
                st.write(f"**Plataforma:** {d['plataforma'] if d['plataforma'] else '-'}")
                st.write(f"**ID solicitação:** {d['id_solicitacao'] if d['id_solicitacao'] else '-'}")
                st.write(f"**Link:** {d['link_solicitacao'] if d['link_solicitacao'] else '-'}")
                st.write(f"**Status:** {status}")
                st.write(f"**Data:** {d['data']}")

            with col2:
                if st.button("✏️ Editar", key=f"editar_dev_{d['id']}", use_container_width=True):
                    st.session_state["devolucao_editar_id"] = int(d["id"])
                    st.session_state["devolucao_excluir_id"] = None

                if st.button("🗑️ Excluir", key=f"excluir_dev_{d['id']}", use_container_width=True):
                    st.session_state["devolucao_excluir_id"] = int(d["id"])
                    st.session_state["devolucao_editar_id"] = None
else:
    st.info("Nenhuma devolução registrada.")

# ---------------------
# EXCLUSÃO DE DEVOLUÇÃO
# ---------------------
devolucao_excluir_id = st.session_state.get("devolucao_excluir_id")

if devolucao_excluir_id is not None:
    st.divider()
    st.subheader("🗑️ Excluir devolução")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            d.id,
            d.produto_id,
            d.quantidade,
            d.elegivel_venda,
            p.codigo
        FROM devolucoes d
        JOIN produtos p ON d.produto_id = p.id
        WHERE d.id = ?
    """, (devolucao_excluir_id,))
    devolucao_excluir = cursor.fetchone()
    conn.close()

    if devolucao_excluir:
        st.warning(
            f"Tem certeza que deseja excluir a devolução do produto **{devolucao_excluir['codigo']}** "
            f"com quantidade **{devolucao_excluir['quantidade']}**?"
        )

        if devolucao_excluir["elegivel_venda"]:
            st.info("Essa devolução foi marcada como elegível para venda. O estoque será ajustado automaticamente.")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button(
                "✅ Confirmar exclusão da devolução",
                key="confirmar_exclusao_devolucao",
                use_container_width=True
            ):
                conn = get_connection()
                cursor = conn.cursor()

                try:
                    # Se a devolução entrou no estoque, remover o impacto antes de apagar
                    if devolucao_excluir["elegivel_venda"]:
                        cursor.execute(
                            "SELECT estoque FROM produtos WHERE id = ?",
                            (devolucao_excluir["produto_id"],)
                        )
                        produto = cursor.fetchone()

                        if produto:
                            estoque_atual = produto["estoque"]
                            novo_estoque = estoque_atual - devolucao_excluir["quantidade"]

                            if novo_estoque < 0:
                                conn.close()
                                st.error("Não foi possível excluir: a operação deixaria o estoque negativo.")
                                st.stop()

                            cursor.execute("""
                                UPDATE produtos
                                SET estoque = ?
                                WHERE id = ?
                            """, (novo_estoque, devolucao_excluir["produto_id"]))

                    cursor.execute(
                        "DELETE FROM devolucoes WHERE id = ?",
                        (devolucao_excluir_id,)
                    )

                    conn.commit()
                    st.success("✅ Devolução excluída com sucesso!")
                    st.session_state["devolucao_excluir_id"] = None
                    st.rerun()

                finally:
                    conn.close()

        with col_btn2:
            if st.button(
                "Cancelar exclusão da devolução",
                key="cancelar_exclusao_devolucao",
                use_container_width=True
            ):
                st.session_state["devolucao_excluir_id"] = None
                st.rerun()

    else:
        st.session_state["devolucao_excluir_id"] = None
        st.warning("Devolução não encontrada para exclusão.")

# -------------------
# EDIÇÃO DE DEVOLUÇÃO
# -------------------
devolucao_editar_id = st.session_state.get("devolucao_editar_id")

if devolucao_editar_id is not None:
    st.divider()
    st.subheader("✏️ Editar devolução")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            motivo,
            observacoes,
            plataforma,
            id_solicitacao,
            link_solicitacao,
            data
        FROM devolucoes
        WHERE id = ?
                """, (devolucao_editar_id,))
    devolucao = cursor.fetchone()
    conn.close()

    if devolucao:
        motivos_opcoes = [
                    "Cliente desistiu",
                    "Produto com defeito",
                    "Produto danificado no transporte",
                    "Erro no envio",
                    "Outro"
                ]
        
        plataformas_opcoes = [
                    "Shopee",
                    "Mercado Livre",
                    "Amazon",
                    "Magalu",
                    "Tik Tok Shop",
                    "Outro"
                ]
        
        motivo_atual = devolucao["motivo"] if devolucao["motivo"] in motivos_opcoes else "Outro"
        plataforma_atual = devolucao["plataforma"] if devolucao["plataforma"] in plataformas_opcoes else "Outro"

        try:
            data_padrao = datetime.strptime(str(devolucao["data"]), "%Y-%m-%d").date()
        except Exception:
            data_padrao = date.today()

        with st.form("form_editar_devolucao"):

            col1, col2 = st.columns(2)

            with col1:
                motivo_edit = st.selectbox(
                    "Motivo da devolução",
                    motivos_opcoes,
                    index=motivos_opcoes.index(motivo_atual)
                )

                observacoes_edit = st.text_input(
                    "Observações",
                    value= devolucao["observacoes"] or "",
                    placeholder="Detalhes adicionais"
                )

                plataforma_edit = st.selectbox(
                    "Plataforma",
                    plataformas_opcoes,
                    index=plataformas_opcoes.index(plataforma_atual)
                )

            with col2:
                id_solicitacao_edit = st.text_input(
                    "ID da solicitação",
                    value=devolucao["id_solicitacao"] or "",
                    placeholder="ABC123"
                )

                link_solicitacao_edit = st.text_input(
                    "Link da solicitação",
                    value=devolucao["link_solicitacao"] or "",
                    placeholder="https://..."
                )

                data_edit = st.date_input(
                    "Data da devolução",
                    value=data_padrao
                )

            col_btn1, col_btn2 = st.columns(2)

            salvar_edicao = col_btn1.form_submit_button(
                "💾 Salvar alterações",
                use_container_width=True
            )

            cancelar_edicao = col_btn2.form_submit_button(
                "Cancelar edição",
                use_container_width=True
            )

        if cancelar_edicao:
            st.session_state["devolucao_editar_id"] = None
            st.rerun()

        if salvar_edicao:
            # padronização
            observacoes_edit = normalizar_texto(observacoes_edit)
            id_solicitacao_edit = normalizar_texto(id_solicitacao_edit).upper()
            link_solicitacao_edit = normalizar_texto(link_solicitacao_edit)

            # validação link
            if link_solicitacao_edit and not (
                link_solicitacao_edit.startswith("http://") or link_solicitacao_edit.startswith("https://")
            ):
                st.error("O link da solicitação deve começar com http:// ou https://")
                st.stop()
        
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE devolucoes
                SET
                    motivo = ?,
                    observacoes = ?,
                    plataforma = ?,
                    id_solicitacao = ?,
                    link_solicitacao = ?,
                    data = ?
                WHERE id = ?
                        """, (
                            motivo_edit,
                            observacoes_edit if observacoes_edit else None,
                            plataforma_edit,
                            id_solicitacao_edit if id_solicitacao_edit else None,
                            link_solicitacao_edit if link_solicitacao_edit else None,
                            data_edit,
                            devolucao_editar_id
                        ))
            conn.commit()
            conn.close()

            st.success("✅ Devolução atualizada com sucesso!")
            st.session_state["devolucao_editar_id"] = None
            st.rerun()
        
    else:
        st.session_state["devolucao_editar_id"] = None
        st.warning("Devolução não encontrada para edição.")