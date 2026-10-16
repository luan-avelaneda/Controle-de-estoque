# Eduluo — Controle de Estoque

Sistema web simples de controle de estoque (projeto acadêmico), feito com **Python, Flask, SQLite, HTML e CSS**.

## Funcionalidades
- Dashboard com indicadores calculados a partir do banco
- Cadastro, edição e desativação de produtos
- Entradas e saídas de estoque (nunca fica negativo, aceita decimais)
- Consulta de estoque com pesquisa, percentual e status por cor
- Notificações de estoque baixo (sino com contador)
- Histórico de movimentações com filtros

## 1. Instalar Python e Git
- Python 3.10 ou superior: https://www.python.org/downloads/ (marque **"Add Python to PATH"** na instalação)
- Git: https://git-scm.com/downloads

Confira no terminal:
```bash
py --version
git --version
```

## 2. Clonar o repositório
```bash
git clone URL_DO_REPOSITORIO
cd eduluo-estoque
```

## 3. Abrir no VS Code
```bash
code .
```
Depois abra o terminal integrado: **Terminal > New Terminal**.

## 4. Criar o ambiente virtual
```bash
py -m venv .venv
```

## 5. Ativar o ambiente virtual
```bash
.venv\Scripts\activate
```
Se o PowerShell bloquear a ativação, execute uma vez:
```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Quando ativo, o terminal mostra `(.venv)` no início da linha.

## 6. Instalar as dependências
```bash
pip install -r requirements.txt
```

## 7. Executar o sistema
```bash
python app.py
```
O banco `estoque.db` é criado automaticamente na primeira execução.

## 8. Acessar no navegador
http://127.0.0.1:5000

## 9. Encerrar
No terminal, pressione `Ctrl + C`. Para sair do ambiente virtual: `deactivate`.

## 10. Git e GitHub — fluxo da equipe

Regra principal: **ninguém altera a `main` diretamente.** Todo trabalho é feito em uma branch própria e entra na `main` por Pull Request.

### Comandos básicos
```bash
git clone URL_DO_REPOSITORIO                      # copia o projeto
git checkout main                                 # vai para a main
git pull origin main                              # atualiza a main local
git checkout -b feature/nome-da-funcionalidade    # cria sua branch
git add .                                         # prepara as alterações
git commit -m "Descrição da alteração"            # registra
git push -u origin feature/nome-da-funcionalidade # envia a branch
```
Dia a dia, antes de continuar o trabalho:
```bash
git checkout feature/nome-da-funcionalidade
git pull origin main        # traz as novidades da main para a sua branch
```

### Como abrir um Pull Request
1. Faça o `push` da sua branch.
2. No GitHub, clique em **Compare & pull request** (ou na aba *Pull requests > New pull request*).
3. Base: `main`; compare: sua branch.
4. Escreva um título e descreva o que foi feito.
5. Peça a revisão de pelo menos um colega.

### Como revisar
1. Abra a aba **Files changed**.
2. Comente linhas específicas, se necessário.
3. Rode o projeto localmente: `git checkout feature/nome-da-branch` e `python app.py`.
4. Clique em **Review changes > Approve** ou **Request changes**.

### Como integrar
Com o PR aprovado e sem conflitos, clique em **Merge pull request**. Depois, todos executam `git checkout main` e `git pull origin main`.

### Conflitos simples
Se o GitHub avisar de conflito:
```bash
git checkout feature/nome-da-funcionalidade
git pull origin main
```
O Git marca os arquivos em conflito assim:
```text
<<<<<<< HEAD
(sua versão)
=======
(versão da main)
>>>>>>> main
```
No VS Code, use **Accept Current / Accept Incoming / Accept Both Changes**, deixe o arquivo correto e remova as marcações. Depois:
```bash
git add .
git commit -m "Resolve conflito com a main"
git push
```
Para evitar conflitos, cada pessoa edita principalmente os próprios arquivos.

## Divisão de tarefas
| Integrante | Responsabilidade | Arquivos principais |
|---|---|---|
| 1 | Produtos e banco de dados | `database.py`, `routes/produtos.py`, `templates/produtos/` |
| 2 | Entradas, saídas e histórico | `routes/movimentacoes.py`, `templates/movimentacoes/` |
| 3 | Dashboard, notificações e visual | `routes/dashboard.py`, `routes/notificacoes.py`, `templates/dashboard.html`, `templates/notificacoes/`, `static/css/style.css` |

O `app.py` e o `base.html` são alterados apenas pelo responsável pela integração, combinado com a equipe.

## Regras de status
- **Normal:** saldo acima de 10% do estoque de referência
- **Estoque baixo:** saldo maior que zero e até 10% da referência
- **Sem estoque:** saldo igual a zero