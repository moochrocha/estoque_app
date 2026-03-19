from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT NOW() AS agora;")
resultado = cursor.fetchone()

print(resultado["agora"])

conn.close()