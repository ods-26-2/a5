"""RF2 - Politica de violacao por zona/EPI."""
from fastapi import APIRouter, HTTPException

from src.a5.modules.politica_violacao.models import NovaPolitica, PoliticaViolacao
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/politica", tags=["politica-violacao"])
service = PoliticaViolacaoService()


@router.post("/zonas/{zona_id}", response_model=PoliticaViolacao)
def definir_politica(zona_id: str, nova: NovaPolitica):
    nova.zona_id = zona_id
    try:
        return service.definir_politica(nova)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/zonas/{zona_id}", response_model=list[PoliticaViolacao])
def listar_politicas(zona_id: str):
    return service.listar_por_zona(zona_id)
