import streamlit as st
import os
import uuid
from mimetypes import guess_type
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
SUPABASE_BUCKET = st.secrets["supabase"]["bucket"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_imagem_produto(arquivo, pasta="produtos"):
    """
    Faz upload da imagem para o Supabase Storage
    e retorna apenas o path salvo no bucket.
    Ex: produtos/550e8400-e29b-41d4-a716-446655440000.webp
    """

    extensao = os.path.splitext(arquivo.name)[1].lower()
    nome_arquivo = f"{uuid.uuid4()}{extensao}"
    caminho_arquivo = f"{pasta}/{nome_arquivo}"

    content_type = arquivo.type
    if not content_type:
        content_type = guess_type(arquivo.name)[0] or "application/octet-stream"

    arquivo.seek(0)
    conteudo = arquivo.read()

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=caminho_arquivo,
        file=conteudo,
        file_options={
            "content-type": content_type,
            "upsert": "false"
        }
    )

    return caminho_arquivo

def get_ulr_publica_imagem(caminho_arquivo):
    if not caminho_arquivo:
        return None
    
    response = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(caminho_arquivo)
    
    if isinstance(response, str):
        return response
    
    if isinstance(response, dict):
        return response.get("publicUrl") or response.get("public_url")
    
    return getattr(response, "public_url", None) or getattr(response, "publicUrl", None)

def remover_imagem(caminho_arquivo):
    if not caminho_arquivo:
        return
    
    supabase.storage_(SUPABASE_BUCKET).remove([caminho_arquivo])