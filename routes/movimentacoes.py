from flask import Blueprint, flash, redirect, render_template, request

import database as db

bp = Blueprint("movimentacoes", __name__)


def _registrar(tipo, template, titulo):
    """Lógica comum de entrada e saída."""
    dados = {"produto_id": request.args.get("produto_id", ""), "quantidade": "", "observacao": ""}

    if request.method == "POST":
        dados = {
            "produto_id": request.form.get("produto_id", "").strip(),
            "quantidade": request.form.get("quantidade", "").strip(),
            "observacao": request.form.get("observacao", "").strip(),
        }
        try:
            produto_id = int(dados["produto_id"])
        except ValueError:
            produto_id = None
        quantidade = db.converter_numero(dados["quantidade"])

        if produto_id is None:
            flash("Selecione um produto.", "erro")
        elif quantidade is None:
            flash("Informe uma quantidade válida (apenas números).", "erro")
        else:
            ok, mensagem = db.registrar_movimentacao(
                produto_id, tipo, quantidade, dados["observacao"]
            )
            flash(mensagem, "sucesso" if ok else "erro")
            if ok:
                return redirect(request.path)

    produtos = db.listar_produtos(somente_ativos=True)
    return render_template(template, titulo=titulo, produtos=produtos, dados=dados)


@bp.route("/entrada", methods=["GET", "POST"])
def entrada():
    return _registrar("entrada", "movimentacoes/entrada.html", "Entrada de estoque")


@bp.route("/saida", methods=["GET", "POST"])
def saida():
    return _registrar("saida", "movimentacoes/saida.html", "Saída de estoque")


@bp.route("/historico")
def historico():
    try:
        produto_id = int(request.args.get("produto_id", ""))
    except ValueError:
        produto_id = None
    tipo = request.args.get("tipo", "")
    if tipo not in ("entrada", "saida"):
        tipo = ""

    movimentacoes = db.listar_movimentacoes(produto_id, tipo)
    return render_template(
        "movimentacoes/historico.html",
        movimentacoes=movimentacoes,
        produtos=db.listar_produtos(),
        filtro_produto=produto_id,
        filtro_tipo=tipo,
    )