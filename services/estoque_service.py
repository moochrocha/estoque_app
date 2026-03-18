from database.connection import get_connection

def get_local_id_por_nome(nome_local):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM locais_estoque WHERE nome = ?", (nome_local,))
    local = cursor.fetchone()

    conn.close()
    return local["id"] if local else None

def criar_estoque_inicial_local(produto_id, quantidade, nome_local="Estoque Local"):
    local_id = get_local_id_por_nome(nome_local)

    if local_id is None:
        return
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO estoque_locais (produto_id, local_id, quantidade)
    VALUES (?, ?, 0)
                   """, (produto_id, local_id))
    
    cursor.execute("""
    UPDATE estoque_locais
    SET quantidade = quantidade + ?
    WHERE produto_id = ? AND local_id = ?
                   """, (quantidade, produto_id, local_id))
    
    conn.commit()
    conn.close()

    recalcular_estoque_total(produto_id)

def recalcular_estoque_total(produto_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(quantidade), 0) AS total
    FROM estoque_locais
    WHERE produto_id = ?
                   """, (produto_id,))
    
    resultado = cursor.fetchone()
    total = resultado["total"] if resultado else 0

    cursor.execute("""
    UPDATE produtos
    SET estoque = ?
    WHERE id = ?
                   """, (total, produto_id))
    
    conn.commit()
    conn.close()

def get_estoques_por_produto(produto_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        l.id AS local_id,
        l.nome AS local_nome,
        COALESCE(e.quantidade, 0) AS quantidade
    FROM locais_estoque l
    LEFT JOIN estoque_locais e
            ON l.id = e.local_id AND e.produto_id = ?
    WHERE l.ativo = 1
    ORDER BY l.nome
    """, (produto_id,))

    dados = cursor.fetchall()
    conn.close()
    return dados