from app import app  # importa sua instância Flask
from models import Usuario

with app.app_context():
    usuario_master = Usuario.query.filter_by(is_master=True).first()

    if usuario_master:
        print(f"🛡️ Usuário master: {usuario_master.username} | Email: {usuario_master.email}")
    else:
        print("❌ Nenhum usuário master encontrado.")
