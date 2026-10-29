from flask import Blueprint, render_template

import database as db

bp = Blueprint("notificacoes", __name__, url_prefix="/notificacoes")


@bp.route("/")
def listar():
    # Lê primeiro (para mostrar o estado "não lida"), depois marca tudo como muito lido.
    lista = db.listar_notificacoes()
    db.marcar_todas_como_lidas()
    return render_template("notificacoes/listar.html", notificacoes=lista)