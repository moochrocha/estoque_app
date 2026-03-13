import streamlit as st
import pandas as pd
from database.connection import get_connection

st.set_page_config(layout="wide")
st.title("📦 Estoque de Produtos")

conn = get_connection()

df = pd.read_sql("SELECT id, imagem, codigo, descricao, categoria, fornecedor, valor_unitario, estoque, data_reposicao FROM produtos", conn)

# -------
# FILTROS
# -------
st.subheader("Filtros")

col1, col2, col3, col4 = st.columns(4)

with col1:
    busca_descricao = st.text_input("Busca por descrição")

with col2:
    busca_codigo = st.text_input("Busca por código")

with col3:
    categorias = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    filtro_categoria = st.selectbox("Categoria", categorias)

with col4:
    fornecedores = ["Todos"] + sorted(df["fornecedor"].dropna().unique().tolist())
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


# ---------------
# EXIBIR PRODUTOS
# ---------------

df_filtrado["valor_unitario"] = df_filtrado["valor_unitario"].fillna(0)
df_filtrado["estoque"] = df_filtrado["estoque"].fillna(0)

total_estoque = int(df_filtrado["estoque"].fillna(0).sum()) if not df_filtrado.empty else 0
total_produtos = len(df_filtrado)
valor_total_estoque = (df_filtrado["valor_unitario"] * df_filtrado["estoque"]).sum() if not df_filtrado.empty else 0

valor_total_formatado = f"R$ {valor_total_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown("## 📊 Resumo")
m1, m2, m3 = st.columns(3)

m1.metric("Produtos encontrados", total_produtos)
m2.metric("Total em estoque", total_estoque)
m3.metric("Valor total em estoque", valor_total_formatado)

st.markdown("---")

# -------------------
# ESTILO DOS CARDS
# -------------------
st.markdown("""
    <style>
    .card-produto {
        border: 1px solid rgba(250,250,250,0.1);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 20px;
        background-color: rgba(255,255,255,0.02);
        min-height: 380px;
    }
    .titulo-produto {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
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
    </style>
""", unsafe_allow_html=True)

# ---------------
# EXIBIR PRODUTOS
# ---------------
st.markdown(f"Produtos encontrados: {len(df_filtrado)}")

if df_filtrado.empty:
    st.warning("Nenhum produto encontrado com os filtros aplicados.")
else:
    colunas = st.columns(3)

    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        with colunas[idx % 3]:

            with st.container():
                st.markdown('<div class="card-produto">', unsafe_allow_html=True)

                if row["imagem"]:
                    st.image(f"images/{row['imagem']}", use_container_width=True)
                else:
                    st.info("Sem imagem")

                st.markdown(
                    f'<div class="titulo-produto">{row["descricao"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Código:</b> {row["codigo"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Categoria:</b> {row["categoria"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Fornecedor:</b> {row["fornecedor"]}</div>',
                    unsafe_allow_html=True
                )

                estoque = row["estoque"] if pd.notnull(row["estoque"]) else 0

                if estoque == 0:
                    classe_estoque = "estoque-zero"
                    texto_estoque = f"Sem estoque ({int(estoque)})"
                elif estoque <= 5:
                    classe_estoque = "estoque-baixo"
                    texto_estoque = f"Estoque baixo ({int(estoque)})"
                else:
                    classe_estoque = "estoque-ok"
                    texto_estoque = f"Estoque disponível ({int(estoque)})"

                st.markdown(
                    f'<div class="texto-card"><b>Estoque:</b> <span class="{classe_estoque}">{texto_estoque}</span></div>',
                    unsafe_allow_html=True
                )

                valor_unitario = row["valor_unitario"] if pd.notnull(row["valor_unitario"]) else 0
                valor_total_item = valor_unitario * estoque

                valor_unitario_formatado = f"R$ {valor_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                valor_total_item_formatado = f"R$ {valor_total_item:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                st.markdown(
                    f'<div class="texto-card"><b>Valor unitário:</b> {valor_unitario_formatado}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Valor total em estoque:</b> {valor_total_item_formatado}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="texto-card"><b>Última reposição:</b> {row["data_reposicao"]}</div>',
                    unsafe_allow_html=True
                )

                st.markdown('</div>', unsafe_allow_html=True)

conn.close()