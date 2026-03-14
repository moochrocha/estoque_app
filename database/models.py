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
    
    conn.commit()
    conn.close()