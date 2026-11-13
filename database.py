"""Acesso ao banco de dados SQLite do Eduluo — Controle de Estoque.

Todo o código que fala com o banco fica neste arquivo.
"""
import math
import sqlite3
from datetime import datetime
from pathlib import Path

CAMINHO_BANCO = Path(__file__).resolve().parent / "estoque.db"

# Alerta de estoque baixo: saldo <= 10% do estoque de referência
LIMITE_ESTOQUE_BAIXO = 0.10

UNIDADES = ["un", "L", "mL", "kg", "g", "m", "cm", "caixa", "pacote", "rolo", "peça"]

TEXTO_STATUS = {
    "normal": "Normal",
    "baixo": "Estoque baixo",
    "sem_estoque": "Sem estoque",
}

MENSAGEM_NOTIFICACAO = {
    "baixo": "Estoque baixo: o saldo atingiu 10% ou menos do estoque de referência.",
    "sem_estoque": "Sem estoque: o produto está com saldo zero.",
}


# ---------------------------------------------------------------------------
# Conexão e criação das tabelas
# ---------------------------------------------------------------------------
def conectar():
    """Abre uma conexão com o banco (linhas acessíveis por nome de coluna)."""
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    """Cria as tabelas na primeira execução."""
    conexao = conectar()
    try:
        with conexao:
            conexao.executescript(
                """
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    unidade TEXT NOT NULL,
                    estoque_referencia REAL NOT NULL CHECK (estoque_referencia > 0),
                    quantidade_atual REAL NOT NULL DEFAULT 0 CHECK (quantidade_atual >= 0),
                    ativo INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
                    quantidade REAL NOT NULL CHECK (quantidade > 0),
                    data_hora TEXT NOT NULL,
                    observacao TEXT,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                );

                CREATE TABLE IF NOT EXISTS notificacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    mensagem TEXT NOT NULL,
                    data_hora TEXT NOT NULL,
                    lida INTEGER NOT NULL DEFAULT 0,
                    ativa INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                );
                CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj TEXT NOT NULL UNIQUE,
                razao_social TEXT NOT NULL,
                nome_fantasia TEXT,
                telefone TEXT,
                email TEXT,
                ativo INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                cpf TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                cargo TEXT,
                email TEXT,
                telefone TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                );
"""
            )
    finally:
        conexao.close()


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def _agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def formatar_numero(valor):
    """35.0 -> '35' | 2.5 -> '2,5' (até 3 casas decimais)."""
    texto = f"{float(valor):.3f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def converter_numero(texto):
    """Converte '12,5' ou '12.5' em float. Retorna None se for inválido."""
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(valor):
        return None
    return round(valor, 3)


def calcular_status(quantidade, referencia):
    """Retorna 'normal', 'baixo' ou 'sem_estoque'."""
    if quantidade <= 0:
        return "sem_estoque"
    if quantidade <= referencia * LIMITE_ESTOQUE_BAIXO + 1e-9:
        return "baixo"
    return "normal"


def calcular_percentual(quantidade, referencia):
    """Percentual = (quantidade atual / estoque de referência) x 100."""
    if referencia <= 0:
        return 0.0
    return quantidade / referencia * 100


def _enriquecer(linha):
    """Converte a linha do banco em dict com percentual e status calculados."""
    produto = dict(linha)
    produto["percentual"] = calcular_percentual(
        produto["quantidade_atual"], produto["estoque_referencia"]
    )
    produto["status"] = calcular_status(
        produto["quantidade_atual"], produto["estoque_referencia"]
    )
    produto["status_texto"] = TEXTO_STATUS[produto["status"]]
    return produto


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
def listar_produtos(busca="", somente_ativos=False):
    sql = "SELECT * FROM produtos WHERE 1 = 1"
    parametros = []
    if busca:
        sql += " AND (codigo LIKE ? OR nome LIKE ?)"
        parametros += [f"%{busca}%", f"%{busca}%"]
    if somente_ativos:
        sql += " AND ativo = 1"
    sql += " ORDER BY nome COLLATE NOCASE"

    conexao = conectar()
    try:
        return [_enriquecer(l) for l in conexao.execute(sql, parametros).fetchall()]
    finally:
        conexao.close()


def buscar_produto(produto_id):
    conexao = conectar()
    try:
        linha = conexao.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return _enriquecer(linha) if linha else None
    finally:
        conexao.close()


def buscar_produto_por_codigo(codigo):
    conexao = conectar()
    try:
        linha = conexao.execute(
            "SELECT * FROM produtos WHERE codigo = ?", (codigo,)
        ).fetchone()
        return _enriquecer(linha) if linha else None
    finally:
        conexao.close()


def criar_produto(codigo, nome, unidade, referencia):
    """Cria o produto com saldo zero. Levanta sqlite3.IntegrityError se o código já existir."""
    conexao = conectar()
    try:
        with conexao:
            cursor = conexao.execute(
                """INSERT INTO produtos
                   (codigo, nome, unidade, estoque_referencia, quantidade_atual, ativo)
                   VALUES (?, ?, ?, ?, 0, 1)""",
                (codigo, nome, unidade, referencia),
            )
            return cursor.lastrowid
    finally:
        conexao.close()


def atualizar_produto(produto_id, codigo, nome, unidade, referencia):
    """Atualiza os dados do produto (o saldo não é alterado aqui)."""
    conexao = conectar()
    try:
        with conexao:
            antigo = conexao.execute(
                "SELECT * FROM produtos WHERE id = ?", (produto_id,)
            ).fetchone()
            conexao.execute(
                """UPDATE produtos
                   SET codigo = ?, nome = ?, unidade = ?, estoque_referencia = ?
                   WHERE id = ?""",
                (codigo, nome, unidade, referencia, produto_id),
            )
            # Se a referência mudou e há saldo, o status pode ter mudado.
            if antigo["estoque_referencia"] != referencia and antigo["quantidade_atual"] > 0:
                _sincronizar_notificacao(conexao, produto_id)
    finally:
        conexao.close()


def alterar_situacao(produto_id, ativo):
    """Ativa (1) ou desativa (0) o produto, mantendo todo o histórico."""
    conexao = conectar()
    try:
        with conexao:
            conexao.execute(
                "UPDATE produtos SET ativo = ? WHERE id = ?", (1 if ativo else 0, produto_id)
            )
    finally:
        conexao.close()


# ---------------------------------------------------------------------------
# Movimentações (entrada e saída)
# ---------------------------------------------------------------------------
def registrar_movimentacao(produto_id, tipo, quantidade, observacao=""):
    """Registra entrada/saída e atualiza o saldo em uma única transação.

    Retorna (True, mensagem) em caso de sucesso ou (False, mensagem) em caso de erro.
    """
    conexao = conectar()
    try:
        with conexao:
            conexao.execute("BEGIN IMMEDIATE")

            produto = conexao.execute(
                "SELECT * FROM produtos WHERE id = ?", (produto_id,)
            ).fetchone()
            if produto is None:
                return False, "Produto não encontrado."
            if not produto["ativo"]:
                return False, "Este produto está inativo e não pode receber movimentações."

            quantidade = round(quantidade, 3)
            if quantidade <= 0:
                return False, "A quantidade deve ser maior que zero."

            unidade = produto["unidade"]
            saldo = produto["quantidade_atual"]

            if tipo == "entrada":
                novo_saldo = round(saldo + quantidade, 3)
            else:
                if quantidade > saldo:
                    return False, (
                        f"Saldo insuficiente. Disponível: {formatar_numero(saldo)} {unidade}; "
                        f"solicitado: {formatar_numero(quantidade)} {unidade}."
                    )
                novo_saldo = round(saldo - quantidade, 3)

            conexao.execute(
                """INSERT INTO movimentacoes (produto_id, tipo, quantidade, data_hora, observacao)
                   VALUES (?, ?, ?, ?, ?)""",
                (produto_id, tipo, quantidade, _agora(), observacao),
            )
            conexao.execute(
                "UPDATE produtos SET quantidade_atual = ? WHERE id = ?",
                (novo_saldo, produto_id),
            )
            _sincronizar_notificacao(conexao, produto_id)

            nome_tipo = "Entrada" if tipo == "entrada" else "Saída"
            return True, (
                f"{nome_tipo} registrada: {formatar_numero(quantidade)} {unidade} de "
                f"{produto['nome']}. Saldo atual: {formatar_numero(novo_saldo)} {unidade}."
            )
    finally:
        conexao.close()


def listar_movimentacoes(produto_id=None, tipo=None):
    """Histórico, das movimentações mais recentes para as mais antigas."""
    sql = """SELECT m.*, p.codigo, p.nome, p.unidade
             FROM movimentacoes m
             JOIN produtos p ON p.id = m.produto_id
             WHERE 1 = 1"""
    parametros = []
    if produto_id:
        sql += " AND m.produto_id = ?"
        parametros.append(produto_id)
    if tipo in ("entrada", "saida"):
        sql += " AND m.tipo = ?"
        parametros.append(tipo)
    sql += " ORDER BY m.data_hora DESC, m.id DESC"

    conexao = conectar()
    try:
        return [dict(l) for l in conexao.execute(sql, parametros).fetchall()]
    finally:
        conexao.close()


# ---------------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------------
def _sincronizar_notificacao(conexao, produto_id):
    """Gera, atualiza ou resolve a notificação do produto (usa a transação em andamento)."""
    produto = conexao.execute(
        "SELECT * FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    status = calcular_status(produto["quantidade_atual"], produto["estoque_referencia"])
    ativa = conexao.execute(
        "SELECT * FROM notificacoes WHERE produto_id = ? AND ativa = 1", (produto_id,)
    ).fetchone()

    if status == "normal":
        if ativa:  # estoque se recuperou: resolve a ocorrência
            conexao.execute("UPDATE notificacoes SET ativa = 0 WHERE id = ?", (ativa["id"],))
        return

    mensagem = MENSAGEM_NOTIFICACAO[status]
    if ativa is None:  # nova ocorrência
        conexao.execute(
            """INSERT INTO notificacoes (produto_id, mensagem, data_hora, lida, ativa)
               VALUES (?, ?, ?, 0, 1)""",
            (produto_id, mensagem, _agora()),
        )
    elif ativa["mensagem"] != mensagem:  # piorou (baixo -> sem estoque): atualiza a mesma
        conexao.execute(
            "UPDATE notificacoes SET mensagem = ?, data_hora = ?, lida = 0 WHERE id = ?",
            (mensagem, _agora(), ativa["id"]),
        )


def contar_nao_lidas():
    conexao = conectar()
    try:
        return conexao.execute(
            "SELECT COUNT(*) FROM notificacoes WHERE lida = 0"
        ).fetchone()[0]
    finally:
        conexao.close()


def listar_notificacoes():
    conexao = conectar()
    try:
        linhas = conexao.execute(
            """SELECT n.*, p.nome, p.codigo, p.unidade, p.quantidade_atual
               FROM notificacoes n
               JOIN produtos p ON p.id = n.produto_id
               ORDER BY n.data_hora DESC, n.id DESC"""
        ).fetchall()
        return [dict(l) for l in linhas]
    finally:
        conexao.close()


def marcar_todas_como_lidas():
    conexao = conectar()
    try:
        with conexao:
            conexao.execute("UPDATE notificacoes SET lida = 1 WHERE lida = 0")
    finally:
        conexao.close()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def resumo_dashboard():
    produtos = listar_produtos()
    conexao = conectar()
    try:
        entradas = conexao.execute(
            "SELECT COUNT(*) FROM movimentacoes WHERE tipo = 'entrada'"
        ).fetchone()[0]
        saidas = conexao.execute(
            "SELECT COUNT(*) FROM movimentacoes WHERE tipo = 'saida'"
        ).fetchone()[0]
    finally:
        conexao.close()

    return {
        "total_produtos": len(produtos),
        "total_baixo": sum(1 for p in produtos if p["status"] == "baixo"),
        "total_sem_estoque": sum(1 for p in produtos if p["status"] == "sem_estoque"),
        "total_entradas": entradas,
        "total_saidas": saidas,
        "produtos": produtos,


# ---------------------------------------------------------------------------
# Empresas
# ---------------------------------------------------------------------------
def listar_empresas(busca="", somente_ativos=False):
    sql = "SELECT * FROM empresas WHERE 1 = 1"
    parametros = []
    if busca:
        sql += " AND (cnpj LIKE ? OR razao_social LIKE ? OR nome_fantasia LIKE ?)"
        parametros += [f"%{busca}%", f"%{busca}%", f"%{busca}%"]
    if somente_ativos:
        sql += " AND ativo = 1"
    sql += " ORDER BY razao_social COLLATE NOCASE"

    conexao = conectar()
    try:
        return [dict(l) for l in conexao.execute(sql, parametros).fetchall()]
    finally:
        conexao.close()

def buscar_empresa(empresa_id):
    conexao = conectar()
    try:
        linha = conexao.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,)).fetchone()
        return dict(linha) if linha else None
    finally:
        conexao.close()

def criar_empresa(cnpj, razao_social, nome_fantasia, telefone, email):
    conexao = conectar()
    try:
        with conexao:
            cursor = conexao.execute(
                """INSERT INTO empresas (cnpj, razao_social, nome_fantasia, telefone, email, ativo)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (cnpj, razao_social, nome_fantasia, telefone, email)
            )
            return cursor.lastrowid
    finally:
        conexao.close()

def atualizar_empresa(empresa_id, cnpj, razao_social, nome_fantasia, telefone, email):
    conexao = conectar()
    try:
        with conexao:
            conexao.execute(
                """UPDATE empresas 
                   SET cnpj = ?, razao_social = ?, nome_fantasia = ?, telefone = ?, email = ?
                   WHERE id = ?""",
                (cnpj, razao_social, nome_fantasia, telefone, email, empresa_id)
            )
    finally:
        conexao.close()

def alterar_situacao_empresa(empresa_id, ativo):
    conexao = conectar()
    try:
        with conexao:
            conexao.execute("UPDATE empresas SET ativo = ? WHERE id = ?", (1 if ativo else 0, empresa_id))
    finally:
        conexao.close()

# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
def listar_usuarios(busca="", empresa_id=None, somente_ativos=False):
    sql = """SELECT u.*, e.razao_social as empresa_nome, e.nome_fantasia as empresa_fantasia 
             FROM usuarios u
             JOIN empresas e ON e.id = u.empresa_id
             WHERE 1 = 1"""
    parametros = []
    if busca:
        sql += " AND (u.cpf LIKE ? OR u.nome LIKE ? OR u.cargo LIKE ?)"
        parametros += [f"%{busca}%", f"%{busca}%", f"%{busca}%"]
    if empresa_id:
        sql += " AND u.empresa_id = ?"
        parametros.append(empresa_id)
    if somente_ativos:
        sql += " AND u.ativo = 1"
    sql += " ORDER BY u.nome COLLATE NOCASE"

    conexao = conectar()
    try:
        return [dict(l) for l in conexao.execute(sql, parametros).fetchall()]
    finally:
        conexao.close()

def buscar_usuario(usuario_id):
    conexao = conectar()
    try:
        linha = conexao.execute(
            """SELECT u.*, e.razao_social as empresa_nome 
               FROM usuarios u 
               JOIN empresas e ON e.id = u.empresa_id 
               WHERE u.id = ?""", 
            (usuario_id,)
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        conexao.close()

def criar_usuario(empresa_id, cpf, nome, cargo, email, telefone):
    conexao = conectar()
    try:
        with conexao:
            cursor = conexao.execute(
                """INSERT INTO usuarios (empresa_id, cpf, nome, cargo, email, telefone, ativo)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (empresa_id, cpf, nome, cargo, email, telefone)
            )
            return cursor.lastrowid
    finally:
        conexao.close()

def atualizar_usuario(usuario_id, empresa_id, cpf, nome, cargo, email, telefone):
    conexao = conectar()
    try:
        with conexao:
            conexao.execute(
                """UPDATE usuarios 
                   SET empresa_id = ?, cpf = ?, nome = ?, cargo = ?, email = ?, telefone = ?
                   WHERE id = ?""",
                (empresa_id, cpf, nome, cargo, email, telefone, usuario_id)
            )
    finally:
        conexao.close()

def alterar_situacao_usuario(usuario_id, ativo):
    conexao = conectar()
    try:
        with conexao:
            conexao.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (1 if ativo else 0, usuario_id))
    finally:
        conexao.close()