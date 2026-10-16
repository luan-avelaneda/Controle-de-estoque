from flask import Blueprint, render_template

import database as db

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    return render_template("dashboard.html", resumo=db.resumo_dashboard())