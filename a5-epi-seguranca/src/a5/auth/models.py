from pydantic import BaseModel

from src.a5.auth.permissions import Papel


class Usuario(BaseModel):
    """Usuario como a API o expoe (nunca inclui senha)."""
    id: str
    nome: str
    papel: Papel
    ativo: bool = True


class NovoUsuario(BaseModel):
    id: str
    nome: str
    papel: Papel
    senha: str | None = None  # sem senha o usuario existe mas nao consegue entrar


class AtualizarUsuario(BaseModel):
    nome: str | None = None
    papel: Papel | None = None
    ativo: bool | None = None
    senha: str | None = None


class LoginRequest(BaseModel):
    id: str
    senha: str


class SessaoOut(BaseModel):
    token: str
    usuario: Usuario
