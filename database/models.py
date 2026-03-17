from database.connection import get_connection

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   codigo TEXT UNIQUE NOT NULL,
                   descricao TEXT,
                   categoria TEXT,
                   fornecedor TEXT,
                   imagem TEXT,
                   estoque INTEGER,
                   valor_unitario REAL,
                   data_reposicao DATE
                   )
                   """)
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentacoes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   produto_id INTEGER,
                   tipo TEXT,
                   quantidade INTEGER,
                   data DATE,
                   observacoes TEXT,
                   local_origme_id INTEGER,
                   local_destino_id INTEGER
                   )
                   """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devolucoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER,
                    motivo TEXT,
                    observacoes TEXT,
                    plataforma TEXT,
                    id_solicitacao TEXT,
                    link_solicitacao TEXT,
                    elegivel_venda INTEGER,
                    data DATE,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locais_estoque (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   nome TEXT UNIQUE NOT NULL,
                   ativo INTEGER DEFAULT 1
                   )
                   """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estoque_locais (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   produto_id INTEGER NOT NULL,
                   local_id INTEGER NOT NULL,
                   quantidade INTEGER NOT NULL DEFAULT 0,
                   UNIQUE(produto_id, local_id)
                   )
                   """)
    
    # inserir locais padrão
    locais_padrao = [
        ("Estoque Local",),
        ("Mercado Livre Full",),
        ("Amazon FBA",)
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO locais_estoque (nome)
    VALUES (?)
                       """, locais_padrao)
    
    conn.commit()
    conn.close()