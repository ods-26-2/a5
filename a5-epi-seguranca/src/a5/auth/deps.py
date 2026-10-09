"""Dependencias FastAPI: quem esta chamando e se o papel pode fazer a acao."""
from typing import Callable

from fastapi import Depends, Header, HTTPException

from src.a5.auth.models import Usuario
from src.a5.auth.permissions import (
    Papel,
    usuario_pode_configurar_politica,
    usuario_pode_ver_relatorios,
)
from src.a5.auth.service import AuthService, get_auth_service
from src.a5.config import settings


def identidade(authorization: str | None = Header(default=None)) -> Usuario | None:
    """Usuario do token Bearer. Sem cabecalho = anonimo (so aceito se A5_EXIGIR_LOGIN=false);
    token invalido ou expirado = 401."""
    if not authorization:
        return None
    esquema, _, token = authorization.partition(" ")
    usuario = get_auth_service().usuario_do_token(token) if esquema.lower() == "bearer" else None
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada.")
    return usuario


def exigir_papel(permitido: Callable[[Papel], bool]):
    def dependencia(usuario: Usuario | None = Depends(identidade)) -> Usuario | None:
        if usuario is None:
            if settings.exigir_login:
                raise HTTPException(status_code=401, detail="Faca login.")
            return None
        if not permitido(usuario.papel):
            raise HTTPException(status_code=403, detail=f"O papel '{usuario.papel.value}' nao tem permissao.")
        return usuario

    return dependencia


def exigir_login(usuario: Usuario | None = Depends(identidade)) -> Usuario | None:
    if usuario is None and settings.exigir_login:
        raise HTTPException(status_code=401, detail="Faca login.")
    return usuario


pode_configurar = exigir_papel(usuario_pode_configurar_politica)
pode_ver_relatorios = exigir_papel(usuario_pode_ver_relatorios)
somente_administrador = exigir_papel(lambda p: p == Papel.ADMINISTRADOR)
