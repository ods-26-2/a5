"""RF2 - Politica de violacao por zona (documento versionado)."""
from fastapi import APIRouter, Depends, HTTPException

from src.a5.auth.deps import exigir_login, pode_configurar

from src.a5.modules.politica_violacao.models import NovaPolitica, PoliticaViolacao
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/politica", tags=["politica-violacao"])
service = PoliticaViolacaoService()


@router.get("", response_model=list[PoliticaViolacao])
def listar_politicas_vigentes(_=Depends(exigir_login)):
    """Politica vigente de cada zona que ja tem uma."""
    return service.listar_vigentes()


@router.post("/zonas/{zona_id}", response_model=PoliticaViolacao)
def definir_politica(zona_id: str, nova: NovaPolitica, _=Depends(pode_configurar)):
    """Cada chamada cria uma nova versao; a zona do caminho prevalece sobre a do corpo."""
    nova.zona.id = zona_id
    try:
        return service.definir_politica(nova)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/zonas/{zona_id}", response_model=PoliticaViolacao)
def politica_vigente(zona_id: str, _=Depends(exigir_login)):
    politica = service.politica_vigente(zona_id)
    if politica is None:
        raise HTTPException(status_code=404, detail="Zona sem politica definida.")
    return politica


@router.get("/zonas/{zona_id}/versoes", response_model=list[PoliticaViolacao])
def listar_versoes(zona_id: str, _=Depends(exigir_login)):
    return service.listar_versoes(zona_id)
