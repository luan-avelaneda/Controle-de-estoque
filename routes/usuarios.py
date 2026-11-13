"""Rotas para o gerenciamento de usuários."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
import sqlite3
import database as db

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

@bp.route("/")
def listar():
    busca = request.args.get("busca", "").strip()
    empresa_id = request.args.get("empresa_id", type=int)
    somente_ativos = request.args.get("ativos") == "1"
    
    usuarios = db.listar_usuarios(busca=busca, empresa_id=empresa_id, somente_ativos=somente_ativos)
    empresas = db.listar_empresas(somente_ativos=True)
    
    return render_template("usuarios/listar.html", usuarios=usuarios, empresas=empresas, busca=busca, empresa_id=empresa_id, somente_ativos=somente_ativos)

@bp.route("/novo", methods=["GET", "POST"])
def novo():
    empresas = db.listar_empresas(somente_ativos=True)
    if not empresas:
        flash("Você precisa cadastrar e ativar pelo menos uma empresa antes de registrar usuários.", "erro")
        return redirect(url_for("empresas.novo"))

    if request.method == "POST":
        empresa_id = request.form.get("empresa_id", type=int)
        cpf = request.form.get("cpf", "").strip()
        nome = request.form.get("nome", "").strip()
        cargo = request.form.get("cargo", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()

        if not empresa_id or not cpf or not nome:
            flash("Empresa, CPF e Nome são obrigatórios.", "erro")
            return render_template("usuarios/formulario.html", titulo="Novo Usuário", dados=request.form, empresas=empresas)

        try:
            db.criar_usuario(empresa_id, cpf, nome, cargo, email, telefone)
            flash("Usuário cadastrado com sucesso!", "sucesso")
            return redirect(url_for("usuarios.listar"))
        except sqlite3.IntegrityError:
            flash(f"O CPF '{cpf}' já está cadastrado.", "erro")

    return render_template("usuarios/formulario.html", titulo="Novo Usuário", dados={}, empresas=empresas)

@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar(usuario_id):
    usuario = db.buscar_usuario(usuario_id)
    if not usuario:
        flash("Usuário não encontrado.", "erro")
        return redirect(url_for("usuarios.listar"))

    empresas = db.listar_empresas(somente_ativos=True)

    if request.method == "POST":
        empresa_id = request.form.get("empresa_id", type=int)
        cpf = request.form.get("cpf", "").strip()
        nome = request.form.get("nome", "").strip()
        cargo = request.form.get("cargo", "").strip()
        email = request.form.get("email", "").strip()
        telefone = request.form.get("telefone", "").strip()

        if not empresa_id or not cpf or not nome:
            flash("Empresa, CPF e Nome são obrigatórios.", "erro")
            return render_template("usuarios/formulario.html", titulo="Editar Usuário", dados=request.form, empresas=empresas, usuario=usuario)

        try:
            db.atualizar_usuario(usuario_id, empresa_id, cpf, nome, cargo, email, telefone)
            flash("Usuário atualizado com sucesso!", "sucesso")
            return redirect(url_for("usuarios.listar"))
        except sqlite3.IntegrityError:
            flash(f"O CPF '{cpf}' já pertence a outro usuário.", "erro")

    return render_template("usuarios/formulario.html", titulo="Editar Usuário", dados=usuario, empresas=empresas, usuario=usuario)

@bp.route("/<int:usuario_id>/situacao", methods=["POST"])
def situacao(usuario_id):
    usuario = db.buscar_usuario(usuario_id)
    if usuario:
        novo_status = 0 if usuario["ativo"] else 1
        db.alterar_situacao_usuario(usuario_id, novo_status)
        status_txt = "ativado" if novo_status else "desativado"
        flash(f"Usuário {status_txt} com sucesso.", "sucesso")
    return redirect(url_for("usuarios.listar"))