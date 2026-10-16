"""Ponto de entrada do Eduluo — Controle de Estoque."""
from datetime import datetime

from flask import Flask

import database as db
from routes import dashboard, movimentacoes, notificacoes, produtos


def criar_app():
    app = Flask(__name__)
    # Chave usada pelo Flask para as mensagens (flash). Projeto acadêmico, uso local.
    app.secret_key = "eduluo-estoque-chave-de-desenvolvimento"

    db.inicializar_banco()

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(produtos.bp)
    app.register_blueprint(movimentacoes.bp)
    app.register_blueprint(notificacoes.bp)

    @app.context_processor
    def dados_comuns():
        # Contador do sino: calculado no banco a cada página carregada
        return {"notificacoes_nao_lidas": db.contar_nao_lidas()}

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