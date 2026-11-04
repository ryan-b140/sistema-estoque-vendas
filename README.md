# Sistema de Controle de Estoque e Vendas

Projeto de uma API para controle de produtos, estoque e vendas, desenvolvido com Python.

## Funcionalidades

- Cadastro, consulta, atualização e exclusão de produtos.
- Controle de quantidade em estoque.
- Registro de vendas.
- Cálculo automático do valor das vendas.
- Histórico de vendas.
- Autenticação de usuários.

## Tecnologias

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT

## Como executar

**1. Clone o repositório**

```bash
git clone https://github.com/ryan-b140/sistema-estoque-vendas.git
```

**2. Entre na pasta**

```bash
cd sistema-estoque-vendas
```

**3. Instale as dependências**

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "python-jose[cryptography]" passlib python-multipart
```

**4. Inicie o servidor**

```bash
uvicorn main:app --reload
```

## Documentação da API

Com o servidor iniciado, acesse:

http://127.0.0.1:8000/docs

A documentação permite testar as funcionalidades da API.

## Objetivo

Projeto desenvolvido para praticar Python, desenvolvimento de APIs, banco de dados e lógica de programação.