"""RF1 - Cadastro do catalogo de EPIs exigidos por zona."""
from fastapi import APIRouter, HTTPException

from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI, NovaEntradaCatalogo
from src.a5.modules.catalogo_epi.service import CatalogoEPIService

router = APIRouter(prefix="/catalogo", tags=["catalogo-epi"])
service = CatalogoEPIService()


@router.get("/epis", response_model=list[EPI])
def listar_epis_disponiveis():
    return service.listar_epis_disponiveis()


@router.get("/zonas/{zona_id}", response_model=list[CatalogoEntrada])
def listar_exigidos_na_zona(zona_id: str):
    return service.listar_exigidos_na_zona(zona_id)


@router.post("/zonas/{zona_id}", response_model=CatalogoEntrada)
def cadastrar_entrada(zona_id: str, entrada: NovaEntradaCatalogo):
    entrada.zona_id = zona_id
    try:
        return service.cadastrar(entrada)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/entradas/{entrada_id}")
def desativar_entrada(entrada_id: str):
    if not service.desativar(entrada_id):
        raise HTTPException(status_code=404, detail="Entrada nao encontrada.")
    return {"status": "desativada"}
