# atualiza_dominios.py
import sqlite3
import os

# Caminho para o banco 'dominios.db'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'dominios.db')

# Conecta ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verifica colunas existentes
cursor.execute("PRAGMA table_info(quarteiroes_conquistados)")
colunas = [col[1] for col in cursor.fetchall()]

if 'categoria' in colunas:
    print("✅ Coluna 'categoria' já existe em quarteiroes_conquistados.")
else:
    try:
        cursor.execute("ALTER TABLE quarteiroes_conquistados ADD COLUMN categoria TEXT")
        conn.commit()
        print("🎉 Coluna 'categoria' adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        print(f"❌ Erro ao adicionar a coluna: {e}")

conn.close()
