"""RF12 - turnos/horarios de monitoramento ativo por zona."""
from fastapi import APIRouter

from src.a5.modules.politica_violacao.models import Turno
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/monitoramento", tags=["monitoramento"])
service = PoliticaViolacaoService()


@router.post("/zonas/{zona_id}/turnos", response_model=Turno)
def definir_turno(zona_id: str, turno: Turno):
    turno.zona_id = zona_id
    return service.definir_turno(turno)


@router.get("/zonas/{zona_id}/turnos", response_model=list[Turno])
def listar_turnos(zona_id: str):
    return service.listar_turnos(zona_id)
