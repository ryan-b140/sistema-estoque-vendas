# Sistema de Controle de Estoque e Vendas

Projeto de uma API para controle de produtos, estoque e vendas, desenvolvido com Python.

## Funcionalidades

- Cadastro, consulta, atualização e exclusão de produtos.
- Controle de quantidade em estoque (a baixa na venda é atômica, sem vender além do estoque).
- Registro de vendas.
- Cálculo automático do valor das vendas, preservado no histórico mesmo se o preço mudar depois.
- Histórico de vendas.
- Autenticação de usuários com JWT.

## Tecnologias

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT (PyJWT)
- pytest

## Como executar

**1. Clone o repositório**

```bash
git clone https://github.com/ryan-b140/sistema-estoque-vendas.git
```

**2. Entre na pasta**

```bash
cd sistema-estoque-vendas
```

**3. Crie o ambiente virtual e instale as dependências**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**4. Inicie o servidor**

```bash
uvicorn main:app --reload
```

## Documentação da API

Com o servidor iniciado, acesse:

http://127.0.0.1:8000/docs

A documentação permite testar as funcionalidades da API.

Um usuário de desenvolvimento é criado automaticamente: **Loja / 1234**.
Para desativar, defina `CRIAR_USUARIO_PADRAO=false`.

## Testes

```bash
pytest -v
```

## Variáveis de ambiente (opcionais)

- `SECRET_KEY`: chave do JWT (obrigatória se `AMBIENTE=producao`)
- `TOKEN_EXPIRA_MINUTOS`: padrão 60
- `DATABASE_URL`: padrão `sqlite:///./estoque_vendas.db`

## Objetivo

Projeto desenvolvido para praticar Python, desenvolvimento de APIs, banco de dados e lógica de programação.
