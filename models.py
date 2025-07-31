from extensions import db  # importa de extensions.py, sem depender de app.py
from datetime import datetime
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    is_master = db.Column(db.Boolean, default=False)


class Conquista(db.Model):
    __bind_key__ = 'dominios'  # 👈 isso liga o modelo ao banco secundário
    id = db.Column(db.Integer, primary_key=True)
    nome_area = db.Column(db.String(80))
    poligono_geojson = db.Column(db.JSON)
    distancia_km = db.Column(db.Float)
    duracao_minutos = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    categoria = db.Column(db.String(50))


# Missões – banco secundário 'dominios'
class Missao(db.Model):
    __bind_key__ = 'dominios'
    __tablename__ = 'missoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    duracao_minutos = db.Column(db.Integer)
    distancia_km = db.Column(db.Float)
    data = db.Column(db.DateTime)



class QuarteiraoConquistado(db.Model):
    __bind_key__ = 'dominios'
    __tablename__ = 'quarteiroes_conquistados'

    id = db.Column(db.Integer, primary_key=True)
    missao_id = db.Column(db.Integer, db.ForeignKey('missoes.id'), nullable=False)
    nome_area = db.Column(db.String(100))
    poligono_geojson = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime)

    # ✅ Relacionamento explícito com Missao
    missao = relationship("Missao", backref="quarteiroes")
