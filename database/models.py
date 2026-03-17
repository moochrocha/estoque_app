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
                   observacoes TEXT
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
    
    conn.commit()
    conn.close()