import psycopg
from psycopg.rows import dict_row
import streamlit as st

def get_connection():
    conn = psycopg.connect(
        host=st.secrets["database"]["host"],
        port=st.secrets["database"]["port"],
        dbname=st.secrets["database"]["name"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        sslmode=st.secrets["database"]["sslmode"],
        row_factory=dict_row
    )
    return conn










# import sqlite3

# def get_connection():
#     conn = sqlite3.connect("estoque.db")
#     conn.row_factory = sqlite3.Row
#     return conn