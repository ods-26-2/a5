"""RF12 - turnos/horarios de monitoramento ativo por zona."""
from fastapi import APIRouter, Depends

from src.a5.auth.deps import exigir_login, pode_configurar
from src.a5.modules.politica_violacao.models import Turno
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/monitoramento", tags=["monitoramento"])
service = PoliticaViolacaoService()


@router.post("/zonas/{zona_id}/turnos", response_model=Turno)
def definir_turno(zona_id: str, turno: Turno, _=Depends(pode_configurar)):
    """Acrescenta um turno a grade da zona."""
    turno.zona_id = zona_id
    return service.definir_turno(turno)


@router.put("/zonas/{zona_id}/turnos", response_model=list[Turno])
def substituir_turnos(zona_id: str, turnos: list[Turno], _=Depends(pode_configurar)):
    """Troca a grade inteira (lista vazia = monitoramento sempre ativo)."""
    return service.substituir_turnos(zona_id, turnos)


@router.get("/zonas/{zona_id}/turnos", response_model=list[Turno])
def listar_turnos(zona_id: str, _=Depends(exigir_login)):
    return service.listar_turnos(zona_id)


@router.get("/zonas/{zona_id}/ativo")
def monitoramento_ativo(zona_id: str, _=Depends(exigir_login)):
    return {"zona_id": zona_id, "ativo": service.monitoramento_ativo(zona_id)}
