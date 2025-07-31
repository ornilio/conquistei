from flask import Flask
from flask_jwt_extended import JWTManager
from flask_login import current_user
from datetime import timedelta
import os
from extensions import db  # Importa instância compartilhada do SQLAlchemy

app = Flask(__name__)
app.secret_key = 'minha_chave_flask_secreta_2025'

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

# 🔐 Configurações do JWT
app.config['JWT_SECRET_KEY'] = 'sua_chave_super_secreta_123'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']        # ✅ Usa cookies em vez de headers
app.config['JWT_COOKIE_SECURE'] = False               # True apenas em produção com HTTPS
#app.config['JWT_COOKIE_SECURE'] = True quando for para producao
app.config['JWT_COOKIE_CSRF_PROTECT'] = False         # Pode ativar depois, se quiser
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'

# 🔌 Inicializa extensões
db.init_app(app)
jwt = JWTManager(app)


    

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
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
    #app.run(debug=True)
