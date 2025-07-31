# 📦 Importações organizadas por categoria

# Flask e utilitários
from flask import Blueprint, render_template, request, redirect, flash, jsonify, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import Missao, QuarteiraoConquistado
import random
from sqlalchemy.orm import selectinload

# JWT (Autenticação)
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, create_access_token,
    set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
)

# Data e arquivos
from datetime import datetime
import os

# Modelos da aplicação
from extensions import db
from models import Usuario, Conquista, Missao, QuarteiraoConquistado

# 🔧 Instância Blueprint
routes = Blueprint("routes", __name__)

# 🏠 Página de login via formulário HTML
@routes.route("/", methods=["GET", "POST"])
def login_page():
    """
    Renderiza a página de login. Processa login via formulário HTML e define cookies JWT.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and check_password_hash(usuario.senha, password):
            access_token = create_access_token(identity=str(usuario.id))
            flash("Login realizado com sucesso!")
            response = make_response(redirect(url_for("routes.home")))
            set_access_cookies(response, access_token)
            return response
        else:
            flash("Usuário ou senha inválidos.")
            return redirect(url_for("routes.login_page"))

    return render_template("login.html", ano=datetime.now().year)

# 🔐 Login via API REST (JSON)
@routes.route("/login", methods=["POST"])
def login_api():
    """
    Autenticação via JSON. Retorna token JWT caso credenciais estejam corretas.
    """
    dados = request.get_json()
    username = dados.get("username")
    senha = dados.get("senha")

    usuario = Usuario.query.filter_by(username=username).first()

    if usuario and check_password_hash(usuario.senha, senha):
        token = create_access_token(identity=usuario.id)
        return jsonify(token=token), 200
    else:
        return jsonify(erro="Usuário ou senha inválidos."), 401

# 📝 Cadastro via formulário HTML
@routes.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """
    Renderiza e processa o cadastro via formulário HTML.
    """
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
        novo_usuario = Usuario(username=username, email=email, senha=senha_hash)

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

# 🏡 Página inicial após login
@routes.route("/home")
def home():
    try:
        # Valida o token JWT
        verify_jwt_in_request()
        usuario_id = get_jwt_identity()
    except Exception as e:
        print("Erro ao verificar token:", e)
        flash("Token inválido ou ausente.")
        return redirect(url_for("routes.login_page"))

    # Busca o usuário pelo ID
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Usuário não encontrado.")
        return redirect(url_for("routes.login_page"))

    # Busca todas as conquistas do usuário via join com Missao
    conquistas = (
        QuarteiraoConquistado.query
        .join(QuarteiraoConquistado.missao)
        .filter(Missao.usuario_id == usuario_id)
        .order_by(QuarteiraoConquistado.timestamp.desc())
        .all()
    )

    # Busca todas as missões do usuário para somar tempo/distância
    missoes = Missao.query.filter_by(usuario_id=usuario_id).all()
    tempo_total = sum(m.duracao_minutos for m in missoes if m.duracao_minutos)
    distancia_total = round(sum(m.distancia_km for m in missoes if m.distancia_km), 2)
    print("Tempo total:", tempo_total)
    # Renderiza o template com os dados
    return render_template(
        "home.html",
        usuario=usuario,
        ano=datetime.now().year,
        conquistas=conquistas,
        tempo_total=tempo_total,
        distancia_total=distancia_total
    )


# 🚪 Logout e remoção de cookies
@routes.route("/logout")
def logout():
    """
    Finaliza a sessão do usuário removendo cookies JWT e redireciona para login.
    """
    response = redirect(url_for("routes.login_page"))
    unset_jwt_cookies(response)
    flash("Sessão encerrada com sucesso!")
    return response

# 🖼️ Upload de avatar do usuário
@routes.route("/upload-avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """
    Permite ao usuário enviar uma nova imagem de avatar.
    """
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)

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

    usuario.avatar = filename
    db.session.commit()

    flash("Avatar atualizado com sucesso!")
    return redirect(url_for("routes.home"))

# 🗺️ Registro de localização e desbloqueio de conquista
@routes.route("/localizacao", methods=["POST"])
@jwt_required()
def receber_localizacao():
    """
    Recebe os dados de localização, duração e distância para registrar uma nova conquista.
    """
    usuario_id = get_jwt_identity()
    dados = request.get_json()

    latitude = dados.get("latitude")
    longitude = dados.get("longitude")
    duracao = dados.get("duracao_minutos")
    distancia = dados.get("distancia_km")

    if not all([latitude, longitude, duracao, distancia]):
        return jsonify({"erro": "Dados incompletos."}), 400

    print(f"Usuário {usuario_id} está em: ({latitude}, {longitude})")
    print(f"⏱️ Tempo: {duracao} min | 📏 Distância: {distancia} km")

    nova_conquista = Conquista(
        usuario_id=int(usuario_id),
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
def nova_conquista():
    try:
        verify_jwt_in_request()
        usuario_id = get_jwt_identity()
    except Exception as e:
        flash("Token inválido.")
        return redirect(url_for("routes.login_page"))

    conquistas = QuarteiraoConquistado.query.join(Missao).filter(
        Missao.usuario_id == usuario_id
    ).all()

    return render_template("nova_conquista.html", usuario_id=usuario_id, conquistas=conquistas)




@routes.route('/editar-perfil')
def editar_perfil():
    # lógica para editar o perfil
    return render_template('editar_perfil.html')

@routes.route('/alterar-senha', methods=['GET', 'POST'])
def alterar_senha():
    # Aqui vai a lógica de alteração de senha
    return render_template('alterar_senha.html')




def gerar_nome_area():
    prefixos = ['Setor', 'Zona', 'Distrito', 'Bloco']
    codigos = ['Alpha', 'Bravo', 'Echo', 'Zeta', 'Delta']
    return f"{random.choice(prefixos)} {random.choice(codigos)}-{random.randint(100,999)}"

@routes.route('/registrar-missao', methods=['POST'])
def registrar_missao_completa():
    dados = request.get_json()
    print("Dados recebidos na missão:", dados)


    # Cria missão
    nova_missao = Missao(
        usuario_id = dados.get('usuario_id'),
        duracao_minutos = dados.get('duracao_minutos'),
        distancia_km = dados.get('distancia_km'),
        data = datetime.utcnow()
    )
    db.session.add(nova_missao)
    db.session.commit()

    # Salva cada área conquistada
    for area in dados.get('conquistas', []):
        quarteirao = QuarteiraoConquistado(
            missao_id = nova_missao.id,
            nome_area = gerar_nome_area(),
            poligono_geojson = area,
            timestamp = datetime.utcnow()
        )
        db.session.add(quarteirao)

    db.session.commit()
    return jsonify({'mensagem': 'Missão e quarteirões salvos com sucesso!'})



@routes.route('/minhas-conquistas', methods=['GET'])
def listar_conquistas():
    usuario_id = request.args.get('usuario_id')  # ou use autenticação com JWT

    conquistas = QuarteiraoConquistado.query.join(Missao).filter(
        Missao.usuario_id == usuario_id
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

