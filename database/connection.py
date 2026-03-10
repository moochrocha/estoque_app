import sqlite3

def get_connection():
    conn = sqlite3.connect("estoque.db")
    conn.row_factory = sqlite3.Row
    return conn