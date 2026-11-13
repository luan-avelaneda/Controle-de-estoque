"""Rotas para o gerenciamento de empresas."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
import sqlite3
import database as db

bp = Blueprint("empresas", __name__, url_prefix="/empresas")

@bp.route("/")
def listar():
    busca = request.args.get("busca", "").strip()
    somente_ativos = request.args.get("ativos") == "1"
    empresas = db.listar_empresas(busca=busca, somente_ativos=somente_ativos)
    return render_template("empresas/listar.html", empresas=empresas, busca=busca, somente_ativos=somente_ativos)

@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        cnpj = request.form.get("cnpj", "").strip()
        razao_social = request.form.get("razao_social", "").strip()
        nome_fantasia = request.form.get("nome_fantasia", "").strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip()

        if not cnpj or not razao_social:
            flash("CNPJ e Razão Social são obrigatórios.", "erro")
            return render_template("empresas/formulario.html", titulo="Nova Empresa", dados=request.form)

        try:
            db.criar_empresa(cnpj, razao_social, nome_fantasia, telefone, email)
            flash("Empresa cadastrada com sucesso!", "sucesso")
            return redirect(url_for("empresas.listar"))
        except sqlite3.IntegrityError:
            flash(f"O CNPJ '{cnpj}' já está cadastrado.", "erro")

    return render_template("empresas/formulario.html", titulo="Nova Empresa", dados={})

@bp.route("/<int:empresa_id>/editar", methods=["GET", "POST"])
def editar(empresa_id):
    empresa = db.buscar_empresa(empresa_id)
    if not empresa:
        flash("Empresa não encontrada.", "erro")
        return redirect(url_for("empresas.listar"))

    if request.method == "POST":
        cnpj = request.form.get("cnpj", "").strip()
        razao_social = request.form.get("razao_social", "").strip()
        nome_fantasia = request.form.get("nome_fantasia", "").strip()
        telefone = request.form.get("telefone", "").strip()
        email = request.form.get("email", "").strip()

        if not cnpj or not razao_social:
            flash("CNPJ e Razão Social são obrigatórios.", "erro")
            return render_template("empresas/formulario.html", titulo="Editar Empresa", dados=request.form, empresa=empresa)

        try:
            db.atualizar_empresa(empresa_id, cnpj, razao_social, nome_fantasia, telefone, email)
            flash("Empresa atualizada com sucesso!", "sucesso")
            return redirect(url_for("empresas.listar"))
        except sqlite3.IntegrityError:
            flash(f"O CNPJ '{cnpj}' já pertence a outra empresa.", "erro")

    return render_template("empresas/formulario.html", titulo="Editar Empresa", dados=empresa, empresa=empresa)

@bp.route("/<int:empresa_id>/situacao", methods=["POST"])
def situacao(empresa_id):
    empresa = db.buscar_empresa(empresa_id)
    if empresa:
        novo_status = 0 if empresa["ativo"] else 1
        db.alterar_situacao_empresa(empresa_id, novo_status)
        status_txt = "ativada" if novo_status else "desativada"
        flash(f"Empresa {status_txt} com sucesso.", "sucesso")
    return redirect(url_for("empresas.listar"))