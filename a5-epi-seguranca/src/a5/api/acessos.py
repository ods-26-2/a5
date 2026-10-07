"""RF9 - perfis de acesso (cadastro simples em memoria, para o time evoluir)."""
from fastapi import APIRouter, HTTPException

from src.a5.auth.models import Usuario
from src.a5.auth.permissions import Papel

router = APIRouter(prefix="/usuarios", tags=["acessos"])

_usuarios: dict[str, Usuario] = {}


@router.post("", response_model=Usuario)
def cadastrar_usuario(usuario: Usuario):
    _usuarios[usuario.id] = usuario
    return usuario


@router.get("", response_model=list[Usuario])
def listar_usuarios():
    return list(_usuarios.values())


@router.get("/{usuario_id}", response_model=Usuario)
def obter_usuario(usuario_id: str):
    usuario = _usuarios.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    return usuario
