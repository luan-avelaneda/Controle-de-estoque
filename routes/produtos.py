import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import database as db

bp = Blueprint("produtos", __name__, url_prefix="/produtos")


def _ler_formulario():
    """Lê e valida o formulário. Retorna (dados, referencia, erros)."""
    dados = {
        "codigo": request.form.get("codigo", "").strip().upper(),
        "nome": request.form.get("nome", "").strip(),
        "unidade": request.form.get("unidade", "").strip(),
        "estoque_referencia": request.form.get("estoque_referencia", "").strip(),
    }
    erros = []

    if not dados["codigo"]:
        erros.append("Informe o código do produto.")
    if not dados["nome"]:
        erros.append("Informe o nome do produto.")
    if dados["unidade"] not in db.UNIDADES:
        erros.append("Selecione uma unidade de medida válida.")

    referencia = db.converter_numero(dados["estoque_referencia"])
    if referencia is None or referencia <= 0:
        erros.append("O estoque de referência deve ser um número maior que zero.")

    return dados, referencia, erros


@bp.route("/")
def listar():
    busca = request.args.get("q", "").strip()
    produtos = db.listar_produtos(busca)
    return render_template("produtos/listar.html", produtos=produtos, busca=busca)


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    dados = {}
    if request.method == "POST":
        dados, referencia, erros = _ler_formulario()
        if not erros and db.buscar_produto_por_codigo(dados["codigo"]):
            erros.append("Já existe um produto com este código.")

        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            try:
                db.criar_produto(dados["codigo"], dados["nome"], dados["unidade"], referencia)
            except sqlite3.IntegrityError:
                flash("Já existe um produto com este código.", "erro")
            else:
                flash("Produto cadastrado com sucesso. Registre uma entrada para adicionar saldo.", "sucesso")
                return redirect(url_for("produtos.listar"))

    return render_template(
        "produtos/formulario.html",
        titulo="Novo produto", produto=None, dados=dados, unidades=db.UNIDADES,
    )


@bp.route("/<int:produto_id>/editar", methods=["GET", "POST"])
def editar(produto_id):
    produto = db.buscar_produto(produto_id)
    if produto is None:
        abort(404)

    dados = {
        "codigo": produto["codigo"],
        "nome": produto["nome"],
        "unidade": produto["unidade"],
        "estoque_referencia": db.formatar_numero(produto["estoque_referencia"]),
    }

    if request.method == "POST":
        dados, referencia, erros = _ler_formulario()
        existente = db.buscar_produto_por_codigo(dados["codigo"]) if dados["codigo"] else None
        if not erros and existente and existente["id"] != produto_id:
            erros.append("Já existe outro produto com este código.")

        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            try:
                db.atualizar_produto(
                    produto_id, dados["codigo"], dados["nome"], dados["unidade"], referencia
                )
            except sqlite3.IntegrityError:
                flash("Já existe outro produto com este código.", "erro")
            else:
                flash("Produto atualizado com sucesso.", "sucesso")
                return redirect(url_for("produtos.listar"))

    return render_template(
        "produtos/formulario.html",
        titulo="Editar produto", produto=produto, dados=dados, unidades=db.UNIDADES,
    )


@bp.route("/<int:produto_id>/alternar", methods=["POST"])
def alternar(produto_id):
    produto = db.buscar_produto(produto_id)
    if produto is None:
        abort(404)

    if produto["ativo"]:
        db.alterar_situacao(produto_id, False)
        flash(f"Produto {produto['nome']} desativado. O histórico foi mantido.", "sucesso")
    else:
        db.alterar_situacao(produto_id, True)
        flash(f"Produto {produto['nome']} reativado.", "sucesso")
    return redirect(url_for("produtos.listar"))