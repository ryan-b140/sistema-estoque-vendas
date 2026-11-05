import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, Numeric, String, create_engine,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# ==========================================
# 1. CONFIGURAÇÕES E SEGURANÇA
# ==========================================
# Em produção defina SECRET_KEY como variável de ambiente.
AMBIENTE = os.getenv("AMBIENTE", "desenvolvimento").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")
if AMBIENTE == "producao" and SECRET_KEY == "chave-de-desenvolvimento-troque-em-producao":
    raise RuntimeError("Defina a variável de ambiente SECRET_KEY antes de rodar em produção.")
ALGORITHM = "HS256"
TOKEN_EXPIRA_MINUTOS = int(os.getenv("TOKEN_EXPIRA_MINUTOS", "60"))

# Em produção defina CRIAR_USUARIO_PADRAO=false
CRIAR_USUARIO_PADRAO = os.getenv("CRIAR_USUARIO_PADRAO", "true").lower() == "true"

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./estoque_vendas.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 2. MODELOS DO BANCO DE DADOS
# ==========================================
class UsuarioDB(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class ProdutoDB(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    codigo_barras = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, index=True, nullable=False)
    descricao = Column(String, default="")
    preco = Column(Numeric(10, 2), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)
    categoria = Column(String, default="")


class VendaDB(Base):
    __tablename__ = "vendas"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade_vendida = Column(Integer, nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)
    data_venda = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    produto = relationship("ProdutoDB")

    @property
    def produto_nome(self) -> str:
        return self.produto.nome if self.produto else ""


Base.metadata.create_all(bind=engine)


# ==========================================
# 3. ESQUEMAS (PYDANTIC)
# ==========================================
# Entrada: Decimal com no máximo 2 casas. Saída: número JSON (float) só na serialização.
DinheiroEntrada = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
DinheiroSaida = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class LoginJSON(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProdutoCreate(BaseModel):
    codigo_barras: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    descricao: str = ""
    preco: DinheiroEntrada
    quantidade: int = Field(ge=0)
    categoria: str = ""


class ProdutoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    descricao: str | None = None
    preco: DinheiroEntrada | None = None
    quantidade: int | None = Field(default=None, ge=0)
    categoria: str | None = None


class ProdutoResponse(ProdutoCreate):
    id: int
    preco: DinheiroSaida
    model_config = ConfigDict(from_attributes=True)


class VendaCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class VendaResponse(BaseModel):
    id: int
    produto_id: int
    produto_nome: str
    quantidade_vendida: int
    valor_total: DinheiroSaida
    data_venda: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator("data_venda")
    @classmethod
    def _assumir_utc(cls, v: datetime) -> datetime:
        # O SQLite devolve datas sem fuso; elas foram gravadas em UTC.
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v


# ==========================================
# 4. DEPENDÊNCIAS E AUXILIARES
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)


def criar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def criar_token(username: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRA_MINUTOS)
    return jwt.encode({"sub": username, "exp": expira}, SECRET_KEY, algorithm=ALGORITHM)


def autenticar(db: Session, username: str, password: str) -> Token:
    """Lógica única de login, usada pelas duas rotas."""
    user = db.query(UsuarioDB).filter(UsuarioDB.username == username).first()
    if not user or not verificar_senha(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=criar_token(user.username))


def obter_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticação inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise erro
    except InvalidTokenError:
        raise erro

    usuario = db.query(UsuarioDB).filter(UsuarioDB.username == username).first()
    if usuario is None:
        raise erro
    return usuario


# ==========================================
# 5. INICIALIZAÇÃO DA API
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if CRIAR_USUARIO_PADRAO:
        db = SessionLocal()
        try:
            if not db.query(UsuarioDB).filter(UsuarioDB.username == "Loja").first():
                db.add(UsuarioDB(username="Loja", hashed_password=criar_hash_senha("1234")))
                db.commit()
                print(">>> Usuário padrão 'Loja' (senha: 1234) criado!")
        finally:
            db.close()
    yield


app = FastAPI(
    title="Sistema de Controle de Estoque e Vendas",
    version="2.0",
    lifespan=lifespan,
)


# ==========================================
# 6. AUTENTICAÇÃO
# ==========================================
@app.post("/token", response_model=Token, tags=["Autenticação"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login OAuth2 (usado pelo botão 'Authorize' do /docs)."""
    return autenticar(db, form_data.username, form_data.password)


@app.post("/login-json", response_model=Token, tags=["Autenticação"])
def login_json(dados: LoginJSON, db: Session = Depends(get_db)):
    """Login simples via JSON: {"username": "Loja", "password": "1234"}."""
    return autenticar(db, dados.username, dados.password)


# ==========================================
# 7. PRODUTOS (CRUD)
# ==========================================
@app.post("/produtos/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED, tags=["Produtos"])
def criar_produto(produto: ProdutoCreate, _: UsuarioDB = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    if db.query(ProdutoDB).filter(ProdutoDB.codigo_barras == produto.codigo_barras).first():
        raise HTTPException(status_code=400, detail="Já existe um produto com este código de barras.")

    novo = ProdutoDB(**produto.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/produtos/", response_model=List[ProdutoResponse], tags=["Produtos"])
def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: UsuarioDB = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    return db.query(ProdutoDB).order_by(ProdutoDB.id).offset(skip).limit(limit).all()


@app.get("/produtos/{produto_id}", response_model=ProdutoResponse, tags=["Produtos"])
def obter_produto(produto_id: int, _: UsuarioDB = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    produto = db.get(ProdutoDB, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@app.put("/produtos/{produto_id}", response_model=ProdutoResponse, tags=["Produtos"])
def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    _: UsuarioDB = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    produto = db.get(ProdutoDB, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    for campo, valor in dados.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto


@app.delete("/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produtos"])
def deletar_produto(produto_id: int, _: UsuarioDB = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    produto = db.get(ProdutoDB, produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    if db.query(VendaDB).filter(VendaDB.produto_id == produto_id).first():
        raise HTTPException(status_code=400, detail="Produto possui vendas registradas e não pode ser excluído.")
    db.delete(produto)
    db.commit()


# ==========================================
# 8. VENDAS E HISTÓRICO
# ==========================================
@app.post("/vendas/", response_model=VendaResponse, status_code=status.HTTP_201_CREATED, tags=["Vendas"])
def realizar_venda(venda: VendaCreate, _: UsuarioDB = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    produto = db.get(ProdutoDB, venda.produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    # Baixa de estoque atômica: só atualiza se ainda houver quantidade suficiente.
    atualizados = (
        db.query(ProdutoDB)
        .filter(ProdutoDB.id == venda.produto_id, ProdutoDB.quantidade >= venda.quantidade)
        .update({ProdutoDB.quantidade: ProdutoDB.quantidade - venda.quantidade}, synchronize_session=False)
    )
    if atualizados == 0:
        db.rollback()
        db.refresh(produto)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estoque insuficiente! Disponível: {produto.quantidade} unidades.",
        )

    nova = VendaDB(
        produto_id=produto.id,
        quantidade_vendida=venda.quantidade,
        valor_total=Decimal(produto.preco) * venda.quantidade,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


@app.get("/vendas/historico", response_model=List[VendaResponse], tags=["Vendas"])
def historico_vendas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: UsuarioDB = Depends(obter_usuario_atual),
    db: Session = Depends(get_db),
):
    return db.query(VendaDB).order_by(VendaDB.data_venda.desc(), VendaDB.id.desc()).offset(skip).limit(limit).all()
