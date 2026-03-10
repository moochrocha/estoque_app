from database.connection import get_connection

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   codigo TEXT UNIQUE,
                   descricao TEXT,
                   categoria TEXT,
                   imagem TEXT,
                   estoque INTEGER,
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