"""RF7, RF8 - painel de supervisao (unico ponto que o front consome)."""
from fastapi import APIRouter

from src.a5.modules.front_supervisao.dto import OcorrenciaSupervisao
from src.a5.modules.front_supervisao.service import FrontSupervisaoService

router = APIRouter(prefix="/supervisao", tags=["front-supervisao"])
service = FrontSupervisaoService()


@router.get("/ocorrencias", response_model=list[OcorrenciaSupervisao])
def listar_ocorrencias(zona_id: str | None = None):
    return service.listar_ocorrencias(zona_id)
