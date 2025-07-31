# 📦 Importações organizadas por categoria

# Flask e utilitários
from flask import Blueprint, render_template, request, redirect, flash, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
from flask_login import login_user, logout_user, current_user, login_required
import os
import random

# Modelos da aplicação
from extensions import db
from models import Usuario, Missao, Conquista, QuarteiraoConquistado

# 🔧 Instância Blueprint
routes = Blueprint("routes", __name__)


def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_master:
            flash("Acesso restrito ao usuário master.")
            return redirect(url_for("routes.home"))
        return f(*args, **kwargs)
    return decorated_function


@routes.route("/painel_adm")
@master_required
def painel_adm():
    filtro = request.args.get("filtro", "").strip()
    if filtro:
        usuarios = Usuario.query.filter(
            (Usuario.username.ilike(f"%{filtro}%")) |
            (Usuario.email.ilike(f"%{filtro}%"))
        ).all()
    else:
        usuarios = Usuario.query.all()
    return render_template("painel_adm.html", usuarios=usuarios)


@routes.route("/toggle_master/<int:usuario_id>")
@master_required
def toggle_master(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        usuario.is_master = not usuario.is_master
        db.session.commit()
        flash("Status de master atualizado.")
    else:
        flash("Usuário não encontrado.")
    return redirect(url_for("routes.painel_adm"))

@routes.route("/excluir_usuario/<int:usuario_id>")
@master_required
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuário excluído com sucesso.")
    else:
        flash("Usuário não encontrado.")
    return redirect(url_for("routes.painel_adm"))


# 🏠 Página de login via formulário HTML

@routes.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and check_password_hash(usuario.senha, password):
            login_user(usuario)
            flash("Login realizado com sucesso!")
            return redirect(url_for("routes.home"))
        else:
            flash("Usuário ou senha inválidos.")
            return redirect(url_for("routes.login_page"))

    return render_template("login.html", ano=datetime.now().year)
@routes.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            flash("As senhas não coincidem.")
            return redirect(url_for("routes.cadastro"))

        usuario_existente = Usuario.query.filter(
            (Usuario.username == username) | (Usuario.email == email)
        ).first()

        if usuario_existente:
            flash("Usuário ou e-mail já cadastrados.")
            return redirect(url_for("routes.cadastro"))

        senha_hash = generate_password_hash(password)
        primeiro_usuario = Usuario.query.first()
        novo_usuario = Usuario(
            username=username,
            email=email,
            senha=senha_hash,
            is_master=False if primeiro_usuario else True
        )

        db.session.add(novo_usuario)
        db.session.commit()
        flash("Cadastro realizado com sucesso!")
        return redirect(url_for("routes.login_page"))

    return render_template("cadastro.html", ano=datetime.now().year)


# 📲 Cadastro via API REST (JSON)
@routes.route("/usuarios", methods=["POST"])
def criar_usuario():
    """
    Cria um novo usuário via API REST. Retorna mensagens de erro ou sucesso em JSON.
    """
    dados = request.get_json()

    username = dados.get("username")
    email = dados.get("email")
    senha = dados.get("senha")
    confirm = dados.get("confirm_senha")

    if not all([username, email, senha, confirm]):
        return jsonify({'erro': 'Campos obrigatórios faltando.'}), 400

    if senha != confirm:
        return jsonify({'erro': 'As senhas não coincidem.'}), 400

    usuario_existente = Usuario.query.filter(
        (Usuario.username == username) | (Usuario.email == email)
    ).first()

    if usuario_existente:
        return jsonify({'erro': 'Usuário ou e-mail já cadastrados.'}), 400

    senha_hash = generate_password_hash(senha)
    novo_usuario = Usuario(username=username, email=email, senha=senha_hash)

    db.session.add(novo_usuario)
    db.session.commit()

    return jsonify({'mensagem': 'Usuário cadastrado com sucesso!'}), 201
@routes.route("/home")
@login_required
def home():
    usuario_id = current_user.id
    missoes = Missao.query.filter_by(usuario_id=usuario_id).all()
    conquistas = (
        QuarteiraoConquistado.query
        .join(QuarteiraoConquistado.missao)
        .filter(Missao.usuario_id == usuario_id)
        .order_by(QuarteiraoConquistado.timestamp.desc())
        .all()
    )

    for conquista in conquistas:
        if conquista.missao:
            conquista.distancia_km = round(conquista.missao.distancia_km or 0, 2)
            conquista.duracao_minutos = conquista.missao.duracao_minutos or 0

    tempo_total = sum(m.duracao_minutos for m in missoes if m.duracao_minutos)
    distancia_total = round(sum(m.distancia_km for m in missoes if m.distancia_km), 2)

    return render_template(
        "home.html",
        usuario=current_user,
        ano=datetime.now().year,
        conquistas=conquistas,
        tempo_total=tempo_total,
        distancia_total=distancia_total
    )

@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com sucesso!")
    return redirect(url_for("routes.login_page"))

@routes.route("/upload-avatar", methods=["POST"])
@login_required
def upload_avatar():
    if "avatar" not in request.files:
        flash("Nenhuma imagem enviada.")
        return redirect(url_for("routes.home"))

    file = request.files["avatar"]
    if file.filename == "":
        flash("Nenhuma imagem selecionada.")
        return redirect(url_for("routes.home"))

    filename = secure_filename(file.filename)
    path = os.path.join("static", "avatars", filename)
    file.save(path)

    current_user.avatar = filename
    db.session.commit()

    flash("Avatar atualizado com sucesso!")
    return redirect(url_for("routes.home"))


# 🗺️ Registro de localização e desbloqueio de conquista
@routes.route("/localizacao", methods=["POST"])
@login_required
def receber_localizacao():
    dados = request.get_json()

    latitude = dados.get("latitude")
    longitude = dados.get("longitude")
    duracao = dados.get("duracao_minutos")
    distancia = dados.get("distancia_km")

    if not all([latitude, longitude, duracao, distancia]):
        return jsonify({"erro": "Dados incompletos."}), 400

    nova_conquista = Conquista(
        usuario_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        nome_area="Área conquistada",
        duracao_minutos=duracao,
        distancia_km=distancia
    )

    db.session.add(nova_conquista)
    db.session.commit()

    return jsonify({"mensagem": "Território registrado com sucesso!"}), 200

# 🏆 Página que celebra a conquista desbloqueada
@routes.route("/nova-conquista")
@login_required
def nova_conquista():
    conquistas = QuarteiraoConquistado.query.join(Missao).filter(
        Missao.usuario_id == current_user.id
    ).all()

    return render_template("nova_conquista.html", usuario_id=current_user.id, conquistas=conquistas)




@routes.route('/editar-perfil')
def editar_perfil():
    # lógica para editar o perfil
    return render_template('editar_perfil.html')

@routes.route('/alterar-senha', methods=['GET', 'POST'])
def alterar_senha():
    # Aqui vai a lógica de alteração de senha
    return render_template('alterar_senha.html')




def gerar_nome_area():
    prefixos = ['Setor', 'Zona', 'Distrito', 'Bloco', 'Região', 'Território']
    codigos = ['Alpha', 'Bravo', 'Echo', 'Zeta', 'Delta', 'Omega', 'Nova']
    complemento = ['Norte', 'Sul', 'Central', 'Leste', 'Oeste']
    return f"{random.choice(prefixos)} {random.choice(codigos)}-{random.randint(100,999)} {random.choice(complemento)}"


@routes.route('/registrar-missao', methods=['POST'])
def registrar_missao_completa():
    dados = request.get_json()
    print("Dados recebidos na missão:", dados)

    # Cria missão
    nova_missao = Missao(
        usuario_id=dados.get('usuario_id'),
        duracao_minutos=dados.get('duracao_minutos'),
        distancia_km=dados.get('distancia_km'),
        data=datetime.utcnow()
    )
    db.session.add(nova_missao)
    db.session.commit()

    # Salva cada área conquistada
    for area_coords in dados.get('conquistas', []):
        pontos = area_coords[0]  # Extrai os pontos [[lng, lat], ...]

        if not pontos or len(pontos) < 2:
            continue  # Ignora se não tem trajeto

        # Remove pontos duplicados (ex: usuário parado)
        pontos_unicos = [p for i, p in enumerate(pontos) if i == 0 or p != pontos[i - 1]]
        if len(pontos_unicos) < 2:
            continue  # Ignora se não houve movimento real

        # Detecta se é Polygon ou LineString
        tipo = "Polygon" if pontos_unicos[0] == pontos_unicos[-1] and len(pontos_unicos) >= 4 else "LineString"
        coordenadas = [pontos_unicos] if tipo == "Polygon" else pontos_unicos

        geojson = {
            "type": "Feature",
            "geometry": {
                "type": tipo,
                "coordinates": coordenadas
            },
            "properties": {
                "categoria": "Área fechada" if tipo == "Polygon" else "Patrulha aberta"
            }
        }

        quarteirao = QuarteiraoConquistado(
            missao_id=nova_missao.id,
            nome_area=gerar_nome_area(),
            poligono_geojson=geojson,
            timestamp=datetime.utcnow()
        )
        db.session.add(quarteirao)

    db.session.commit()
    return jsonify({'mensagem': 'Missão salva com sucesso!'})

@routes.route("/minhas-conquistas", methods=["GET"])
@login_required
def listar_conquistas():
    conquistas = QuarteiraoConquistado.query.join(Missao).filter(
        Missao.usuario_id == current_user.id
    ).all()

    resultado = [{
        'id': c.id,
        'nome_area': c.nome_area,
        'coordenadas': c.poligono_geojson,
        'timestamp': c.timestamp.isoformat(),
        'distancia_km': c.missao.distancia_km,
        'duracao_minutos': c.missao.duracao_minutos,
        'categoria': getattr(c, 'categoria', None)
    } for c in conquistas]

    return jsonify(resultado), 200
