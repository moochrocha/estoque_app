from database.connection import get_connection

def get_local_id_por_nome(nome_local):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM locais_estoque WHERE nome = ?", (nome_local,))
    local = cursor.fetchone()
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
    total = cursor.fetchone(["total"])

    cursor.execute("""
    UPDATE produtos
    SET estoque = ?
    WHERE id = ?
                   """, (total, produto_id))
    
    conn.commit()
    conn.close()
