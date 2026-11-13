"""Ponto de entrada do Eduluo — Controle de Estoque."""
from datetime import datetime

from flask import Flask, redirect, request, session, url_for

import database as db
from routes import auth, dashboard, movimentacoes, notificacoes, produtos, empresas, usuarios

# Páginas que podem ser abertas sem estar logado
ROTAS_PUBLICAS = {"auth.login", "auth.cadastro", "static"}


def criar_app():
    app = Flask(__name__)
    # Chave usada pelo Flask para as mensagens (flash). Projeto acadêmico, uso local.
    app.secret_key = "eduluo-estoque-chave-de-desenvolvimento"

    db.inicializar_banco()

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(produtos.bp)
    app.register_blueprint(movimentacoes.bp)
    app.register_blueprint(notificacoes.bp)
    app.register_blueprint(empresas.bp)         # Adicionado
    app.register_blueprint(usuarios.bp)         # Adicionado

    @app.before_request
    def exigir_login():
        """Toda página do sistema exige login; sem sessão, vai para a tela de login."""
        if request.endpoint in ROTAS_PUBLICAS:
            return None
        conta_id = session.get("conta_id")
        if conta_id and db.buscar_conta(conta_id):
            return None
        session.clear()
        # Guarda a página pedida para voltar a ela depois do login
        proximo = request.full_path.rstrip("?") if request.method == "GET" else ""
        if proximo == "/":
            proximo = ""
        return redirect(url_for("auth.login", proximo=proximo or None))

    @app.context_processor
    def dados_comuns():
        if not session.get("conta_id"):
            return {"notificacoes_nao_lidas": 0, "conta_nome": None}
        # Contador do sino: calculado no banco a cada página carregada
        return {
            "notificacoes_nao_lidas": db.contar_nao_lidas(),
            "conta_nome": session.get("conta_nome"),
        }

    @app.template_filter("numero")
    def filtro_numero(valor):
        return db.formatar_numero(valor)

    @app.template_filter("percentual")
    def filtro_percentual(valor):
        return f"{valor:.1f}".replace(".", ",") + "%"

    @app.template_filter("data_br")
    def filtro_data_br(texto):
        return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")

    return app


app = criar_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)