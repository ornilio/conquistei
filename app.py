from flask import Flask
from flask_login import LoginManager, current_user
import os
from extensions import db  # Importa instância compartilhada do SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'minha_chave_flask_secreta_2025'  # Recomendo substituir por algo mais forte em produção

# 📁 Caminho absoluto para o banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'usuarios.db')
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

# Banco secundário para missões e conquistas
db_dominios_path = os.path.join(basedir, 'instance', 'dominios.db')
app.config['SQLALCHEMY_BINDS'] = {
    'dominios': f'sqlite:///{db_dominios_path}'
}

# 🔧 Configurações gerais da aplicação
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔌 Inicializa extensões
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import Usuario
    return Usuario.query.get(int(user_id))

# 💡 Injeta current_user nos templates
@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)

with app.app_context():
    from models import Usuario
    from routes import routes
    db.create_all()
    app.register_blueprint(routes)

# 🚀 Executa aplicação Flask
if __name__ == "__main__":
    app.run(debug=True)
