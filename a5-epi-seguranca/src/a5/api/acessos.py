"""RF9 - login, sessao e cadastro de usuarios com perfis."""
from fastapi import APIRouter, Depends, Header, HTTPException

from src.a5.auth.deps import identidade, somente_administrador
from src.a5.auth.models import (
    AtualizarUsuario,
    LoginRequest,
    NovoUsuario,
    SessaoOut,
    Usuario,
)
from src.a5.auth.service import get_auth_service

router = APIRouter(tags=["acessos"])


@router.post("/auth/login", response_model=SessaoOut)
def login(req: LoginRequest):
    sessao = get_auth_service().login(req.id, req.senha)
    if sessao is None:
        raise HTTPException(status_code=401, detail="Usuario ou senha invalidos.")
    token, usuario = sessao
    return SessaoOut(token=token, usuario=usuario)


@router.get("/auth/eu", response_model=Usuario)
def quem_sou_eu(usuario: Usuario | None = Depends(identidade)):
    if usuario is None:
        raise HTTPException(status_code=401, detail="Faca login.")
    return usuario


@router.post("/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization:
        get_auth_service().logout(authorization.partition(" ")[2])
    return {"status": "encerrada"}


@router.get("/usuarios", response_model=list[Usuario])
def listar_usuarios(_=Depends(somente_administrador)):
    return get_auth_service().listar()


@router.post("/usuarios", response_model=Usuario)
def cadastrar_usuario(novo: NovoUsuario, _=Depends(somente_administrador)):
    try:
        return get_auth_service().cadastrar(novo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/usuarios/{usuario_id}", response_model=Usuario)
def obter_usuario(usuario_id: str, _=Depends(somente_administrador)):
    usuario = get_auth_service().obter(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    return usuario


@router.patch("/usuarios/{usuario_id}", response_model=Usuario)
def atualizar_usuario(usuario_id: str, dados: AtualizarUsuario, _=Depends(somente_administrador)):
    try:
        return get_auth_service().atualizar(usuario_id, dados)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
