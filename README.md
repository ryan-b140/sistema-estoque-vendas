# 📦 Sistema de Controle de Estoque e Vendas (FastAPI)

API RESTful moderna e segura desenvolvida com **FastAPI** e **SQLAlchemy**, projetada para a gestão eficiente de inventário, registo de produtos, transações de vendas e controlo de histórico.

## 🚀 Tecnologias Utilizadas
- **Python** (Linguagem principal)
- **FastAPI** (Framework web de alta performance)
- **SQLAlchemy & SQLite** (ORM e Base de dados local)
- **Pydantic** (Validação de dados rigorosa)
- **JWT & Passlib** (Autenticação segura baseada em tokens e hash de palavras-passe)

## ✨ Funcionalidades Principais
- **Autenticação Dupla**: Suporte a OAuth2 padrão (botão *Authorize* do Swagger) e um login simplificado via JSON (`/login-json`) para testes rápidos.
- **Utilizador Automático**: Criação automática de um utilizador de teste (`Loja` / `1234`) no arranque da aplicação para facilitar os primeiros testes.
- **CRUD de Produtos**: Gestão completa de inventário com validação de códigos de barras, preços monetários precisos (`Decimal`) e categorias.
- **Registo de Vendas Inteligente**: Validação atómica de stock em tempo real (impede vendas superiores à quantidade disponível) e cálculo automático do valor total.
- **Histórico de Transações**: Consulta de vendas passadas ordenada por data de forma imutável.

## ⚙️ Como Executar o Projeto Localmente

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/ryan-b140/sistema-estoque-vendas.git](https://github.com/ryan-b140/sistema-estoque-vendas.git)
   cd sistema-estoque-vendas