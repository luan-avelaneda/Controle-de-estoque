"""Rotas de acesso ao sistema: login, cadastro de conta e saída."""
import re
import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import database as db

bp = Blueprint("auth", __name__)

TAMANHO_MINIMO_SENHA = 6
PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _destino_seguro(destino):
    """Aceita apenas caminhos internos (evita redirecionar para outro site)."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("dashboard.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("conta_id"):
        return redirect(url_for("dashboard.index"))

    proximo = request.values.get("proximo", "")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")

        conta = db.autenticar_conta(email, senha) if email and senha else None
        if conta is None:
            flash("E-mail ou senha incorretos.", "erro")
            return render_template("auth/login.html", email=email, proximo=proximo)

        session.clear()
        session["conta_id"] = conta["id"]
        session["conta_nome"] = conta["nome"]
        return redirect(_destino_seguro(proximo))

    return render_template("auth/login.html", email="", proximo=proximo)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if session.get("conta_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        erro = None
        if not nome or not email or not senha:
            erro = "Preencha nome, e-mail e senha."
        elif not PADRAO_EMAIL.match(email):
            erro = "Informe um e-mail válido."
        elif len(senha) < TAMANHO_MINIMO_SENHA:
            erro = f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres."
        elif senha != confirmacao:
            erro = "As senhas não conferem."

        if erro is None:
            try:
                db.criar_conta(nome, email, senha)
            except sqlite3.IntegrityError:
                erro = "Já existe uma conta com este e-mail."

        if erro:
            flash(erro, "erro")
            return render_template("auth/cadastro.html", nome=nome, email=email)

        flash("Conta criada! Entre com seu e-mail e senha.", "sucesso")
        return redirect(url_for("auth.login"))

    return render_template("auth/cadastro.html", nome="", email="")


@bp.route("/sair", methods=["POST"])
def sair():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("auth.login"))
