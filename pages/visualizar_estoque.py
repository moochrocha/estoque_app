from datetime import datetime
import unicodedata

import streamlit as st
import psycopg
import pandas as pd
from database.connection import get_connection
from services.estoque_service import get_estoques_por_produto
from services.auth import require_login, render_sidebar_logout
from services.storage_service import (
    get_url_publica_imagem,
    upload_imagem_produto,
    remover_imagem
)

st.set_page_config(
    page_title="Estoque de produtos",
    page_icon="📦",
    layout="wide"
)

# -----
# LOGIN
# -----
require_login()
render_sidebar_logout()

st.title("📦 Estoque de Produtos")

# -----------
# FUNÇÕES AUX
# -----------
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=60)
def carregar_produtos():
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                imagem,
                codigo,
                descricao,
                categoria,
                fornecedor,
                valor_unitario,
                estoque,
                data_reposicao
            FROM produtos
            ORDER BY id
        """)

        dados = cursor.fetchall()

        df_local = pd.DataFrame(dados)
        return df_local
    finally:
        conn.close()

    if not df_local.empty:
        df_local["id"] = pd.to_numeric(df_local["id"], errors="coerce")
        df_local["valor_unitario"] = pd.to_numeric(df_local["valor_unitario"], errors="coerce").fillna(0)
        df_local["estoque"] = pd.to_numeric(df_local["estoque"], errors="coerce").fillna(0)

        df_local["descricao"] = df_local["descricao"].fillna("").astype(str)
        df_local["codigo"] = df_local["codigo"].fillna("").astype(str)
        df_local["categoria"] = df_local["categoria"].fillna("").astype(str)
        df_local["fornecedor"] = df_local["fornecedor"].fillna("").astype(str)
        df_local["imagem"] = df_local["imagem"].fillna("").astype(str)

    return df_local

def normalizar_texto(texto):
    return " ".join(texto.strip().split())

def remover_acentos(texto):
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )

ORDEM_LOCAIS = [
    "Estoque Local",
    "Mercado Livre Full",
    "Amazon FBA"
]

MAPA_LOCAIS = {
    "Estoque Local": "Local",
    "Mercado Livre Full": "ML FULL ⚡",
    "Amazon FBA": "AMZ FBA"
}

# -----------------------
# CSS
# -----------------------
st.markdown("""
<style>
.img-placeholder {
    width: 100%;
    aspect-ratio: 1 / 1;
    border: 1px dashed rgba(250,250,250,0.18);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(255,255,255,0.02);
    color: #bdbdbd;
    font-size: 16px;
    margin-bottom: 12px;
    text-align: center;
}

.titulo-produto {
    font-size: 20px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 10px;
}

.texto-card {
    font-size: 14px;
    margin-bottom: 6px;
}

.estoque-ok {
    color: #16a34a;
    font-weight: 700;
}

.estoque-baixo {
    color: #f59e0b;
    font-weight: 700;
}

.estoque-zero {
    color: #ef4444;
    font-weight: 700;
}
            
.image-container {
    width: 100%;
    aspect-ratio: 1 / 1;
    background: linear-gradient(145deg, #1f2937, #111827);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
}

.image-container img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}
</style>
""", unsafe_allow_html=True)

# ----------
# ESTADO
# ----------
if "produto_editar_id" not in st.session_state:
    st.session_state["produto_editar_id"] = None

if "produto_excluir_id" not in st.session_state:
    st.session_state["produto_excluir_id"] = None

# ---------------
# CARREGAR DADOS
# ---------------
df = carregar_produtos()

if not df.empty:
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["valor_unitario"] = pd.to_numeric(df["valor_unitario"], errors="coerce").fillna(0)
    df["estoque"] = pd.to_numeric(df["estoque"], errors="coerce").fillna(0)

# -------
# FILTROS
# -------
st.subheader("Filtros")

col1, col2, col3, col4 = st.columns(4)

with col1:
    busca_descricao = st.text_input("Busca por descrição", placeholder="Descrição desejada")

with col2:
    busca_codigo = st.text_input("Busca por código", placeholder="Código desejado")

with col3:
    categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist()) if not df.empty else ["Todas"]
    filtro_categoria = st.selectbox("Categoria", categorias)

with col4:
    fornecedores = ["Todos"] + sorted(df["fornecedor"].dropna().unique().tolist()) if not df.empty else ["Todos"]
    filtro_fornecedor = st.selectbox("Fornecedor", fornecedores)

# -------
# APLICAR FILTROS
# -------
df_filtrado = df.copy()

if busca_descricao:
    df_filtrado = df_filtrado[
        df_filtrado["descricao"].str.contains(busca_descricao, case=False, na=False)
    ]

if busca_codigo:
    df_filtrado = df_filtrado[
        df_filtrado["codigo"].str.contains(busca_codigo, case=False, na=False)
    ]

if filtro_categoria != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["categoria"] == filtro_categoria
    ]

if filtro_fornecedor != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["fornecedor"] == filtro_fornecedor
    ]

# -------------
# MÉTRICAS
# -------------
total_estoque = int(float(df_filtrado["estoque"].sum())) if not df_filtrado.empty else 0
total_produtos = len(df_filtrado)
valor_total_estoque = (df_filtrado["valor_unitario"] * df_filtrado["estoque"]).sum() if not df_filtrado.empty else 0

st.markdown("## 📊 Resumo")
m1, m2, m3 = st.columns(3)

m1.metric("Produtos encontrados", total_produtos)
m2.metric("Total em estoque", total_estoque)
m3.metric("Valor total em estoque", formatar_moeda(valor_total_estoque))

st.markdown("---")

# -----------
# LISTAGEM
# -----------
st.markdown(f"## 🛍️ Produtos encontrados: {len(df_filtrado)}")

if df_filtrado.empty:
    st.warning("Nenhum produto encontrado com os filtros aplicados.")
else:
    colunas = st.columns(3)

    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        with colunas[idx % 3]:
            with st.container(border=True):

                estoques_locais = get_estoques_por_produto(int(row["id"]))

                if pd.notnull(row["imagem"]) and row["imagem"]:
                    url_imagem = get_url_publica_imagem(row["imagem"])

                    if url_imagem:
                        st.markdown(
                            f"""
                            <div class="image-container">
                                <img src="{url_imagem}">
                            </div>
                            """,
                            unsafe_allow_html=True)
                    else:   
                        st.markdown('<div class="img-placeholder">Imagem indisponível</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        """
                        <div class="image-container">
                            <span style="color:#999;">Sem imagem</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f'<div class="titulo-produto">{row["descricao"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(f'<div class="texto-card"><b>Código:</b> {row["codigo"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="texto-card"><b>Categoria:</b> {row["categoria"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="texto-card"><b>Fornecedor:</b> {row["fornecedor"]}</div>', unsafe_allow_html=True)

                estoque = int(row["estoque"]) if pd.notnull(row["estoque"]) else 0

                if estoque == 0:
                    classe_estoque = "estoque-zero"
                    texto_estoque = f"Sem estoque ({estoque})"
                elif estoque <= 5:
                    classe_estoque = "estoque-baixo"
                    texto_estoque = f"Estoque baixo ({estoque})"
                else:
                    classe_estoque = "estoque-ok"
                    texto_estoque = f"Estoque disponível ({estoque})"

                st.markdown(
                    f'<div class="texto-card"><b>Estoque total:</b> <span class="{classe_estoque}">{texto_estoque}</span></div>',
                    unsafe_allow_html=True
                )

                estoques_locais_ordenados = sorted(
                    estoques_locais,
                    key=lambda x: ORDEM_LOCAIS.index(x["local_nome"]) if x["local_nome"] in ORDEM_LOCAIS else 999
                )

                for e in estoques_locais_ordenados:
                    nome_formatado = MAPA_LOCAIS.get(e["local_nome"], e["local_nome"])
                    st.markdown(
                        f'<div class="texto-card">• <b>{nome_formatado}:</b> {e["quantidade"]}</div>',
                        unsafe_allow_html=True
                    )

                valor_unitario = float(row["valor_unitario"]) if pd.notnull(row["valor_unitario"]) else 0.0
                valor_total_item = valor_unitario * estoque

                st.markdown(
                    f'<div class="texto-card"><b>Valor unitário:</b> {formatar_moeda(valor_unitario)}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Valor total em estoque:</b> {formatar_moeda(valor_total_item)}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Última reposição:</b> {row["data_reposicao"]}</div>',
                    unsafe_allow_html=True
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✏️ Editar", key=f"editar_{row['id']}", use_container_width=True):
                        st.session_state["produto_editar_id"] = int(row["id"])
                        st.session_state["produto_excluir_id"] = None

                with col_btn2:
                    if st.button("🗑️ Excluir", key=f"excluir_{row['id']}", use_container_width=True):
                        st.session_state["produto_excluir_id"] = int(row["id"])
                        st.session_state["produto_editar_id"] = None

# --------------
# FORMS DE EDIÇÃO
# --------------
produto_editar_id = st.session_state.get("produto_editar_id")

if produto_editar_id is not None:
    st.markdown("---")
    st.markdown("## ✏️ Editar produto")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            codigo,
            descricao,
            categoria,
            fornecedor,
            valor_unitario,
            data_reposicao,
            imagem
        FROM produtos
        WHERE id = %s
    """, (produto_editar_id,))
    produto = cursor.fetchone()
    conn.close()

    if produto:
        with st.form("form_editar_produto"):
            col_a, col_b = st.columns(2)

            with col_a:
                novo_codigo = st.text_input("Código do produto", value=produto["codigo"])
                nova_descricao = st.text_input("Descrição", value=produto["descricao"])
                nova_categoria = st.text_input("Categoria", value=produto["categoria"] or "")
                novo_fornecedor = st.text_input("Fornecedor", value=produto["fornecedor"] or "")

            with col_b:
                novo_valor_unitario = st.number_input(
                    "Valor unitário",
                    min_value=0.0,
                    value=float(produto["valor_unitario"] or 0),
                    format="%.2f"
                )

                data_atual = produto["data_reposicao"]

                try:
                    data_formatada = datetime.strptime(str(data_atual), "%Y-%m-%d").date()
                except Exception:
                    data_formatada = datetime.today().date()

                nova_data_reposicao = st.date_input(
                    "Data última reposição",
                    value=data_formatada
                )

            nova_imagem = st.file_uploader(
                "Alterar imagem do produto (opcional)",
                type=["png", "jpg", "jpeg", "webp"]
            )

            st.info("O estoque é controlado por local e deve ser ajustado na tela de movimentação de estoque.")

            col_btn1, col_btn2 = st.columns(2)
            salvar = col_btn1.form_submit_button("💾 Salvar alterações")
            cancelar = col_btn2.form_submit_button("Cancelar edição")

        if cancelar:
            st.session_state["produto_editar_id"] = None
            st.rerun()

        if salvar:
            novo_codigo = normalizar_texto(novo_codigo).upper()
            nova_descricao = normalizar_texto(nova_descricao)
            nova_categoria = remover_acentos(normalizar_texto(nova_categoria)).title()
            novo_fornecedor = remover_acentos(normalizar_texto(novo_fornecedor)).title()

            if not novo_codigo:
                st.error("O código do produto é obrigatório.")
                st.stop()

            if not nova_descricao:
                st.error("A descrição do produto é obrigatória.")
                st.stop()

            if not nova_categoria:
                st.error("A categoria do produto é obrigatória.")
                st.stop()

            if not novo_fornecedor:
                st.error("O fornecedor do produto é obrigatório.")
                st.stop()

            nome_imagem = produto["imagem"]

            if nova_imagem is not None:
                caminho_antigo = produto["imagem"]
                nome_imagem = upload_imagem_produto(nova_imagem, pasta="produtos_imagens")

                if caminho_antigo:
                    try:
                        remover_imagem(caminho_antigo)
                    except Exception:
                        pass

            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE produtos
                    SET
                        codigo = %s,
                        descricao = %s,
                        categoria = %s,
                        fornecedor = %s,
                        valor_unitario = %s,
                        data_reposicao = %s,
                        imagem = %s
                    WHERE id = %s
                """, (
                    novo_codigo,
                    nova_descricao,
                    nova_categoria,
                    novo_fornecedor,
                    novo_valor_unitario,
                    nova_data_reposicao,
                    nome_imagem,
                    produto_editar_id
                ))
                conn.commit()

                st.success("Produto atualizado com sucesso!")
                st.session_state["produto_editar_id"] = None
                st.rerun()

            except psycopg.IntegrityError:
                conn.rollback()
                st.error("Já existe um produto com esse código.")

            finally:
                conn.close()

    else:
        st.session_state["produto_editar_id"] = None
        st.warning("Produto não encontrado para edição.")

# -----------------
# FORMS DE EXCLUSÃO
# -----------------
produto_excluir_id = st.session_state.get("produto_excluir_id")

if produto_excluir_id is not None:
    st.markdown("---")
    st.markdown("## 🗑️ Excluir produto")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, codigo, descricao, imagem
        FROM produtos
        WHERE id = %s
    """, (produto_excluir_id,))
    produto_excluir = cursor.fetchone()
    conn.close()

    if produto_excluir:
        st.warning(
            f"Tem certeza que deseja excluir o produto **{produto_excluir['descricao']}** "
            f"(código: **{produto_excluir['codigo']}**) ?"
        )

        col_del1, col_del2 = st.columns(2)

        with col_del1:
            if st.button("✅ Confirmar exclusão", key="confirmar_exclusao", use_container_width=True):
                conn = get_connection()
                cursor = conn.cursor()

                if produto_excluir["imagem"]:
                    try:
                        remover_imagem(produto_excluir["imagem"])
                    except Exception:
                        pass

                cursor.execute("DELETE FROM estoque_locais WHERE produto_id = %s", (produto_excluir_id,))
                cursor.execute("DELETE FROM movimentacoes WHERE produto_id = %s", (produto_excluir_id,))
                cursor.execute("DELETE FROM devolucoes WHERE produto_id = %s", (produto_excluir_id,))
                cursor.execute("DELETE FROM produtos WHERE id = %s", (produto_excluir_id,))

                conn.commit()
                conn.close()

                st.success("Produto excluído com sucesso!")
                st.session_state["produto_excluir_id"] = None
                st.session_state["produto_editar_id"] = None
                st.rerun()

        with col_del2:
            if st.button("Cancelar exclusão", key="cancelar_exclusao", use_container_width=True):
                st.session_state["produto_excluir_id"] = None
                st.rerun()

    else:
        st.session_state["produto_excluir_id"] = None
        st.warning("Produto não encontrado para exclusão.")