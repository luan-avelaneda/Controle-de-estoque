from flask import Blueprint, render_template, request, redirect, flash, session

bp = Blueprint("login", __name__)

@bp.route("/login", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        # Acessos de demonstração para o trabalho
        if usuario == "admin" and senha == "123456":
            session["usuario"] = usuario
            return redirect("/")

        flash("Usuário ou senha incorretos.")

    return render_template("login.html")