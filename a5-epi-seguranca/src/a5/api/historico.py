"""RF10, RF11 - relatorios analiticos e historico com filtros."""
from fastapi import APIRouter

from src.a5.modules.gestao_alertas.models import ReconhecimentoRegistrado
from src.a5.modules.gestao_alertas.service import GestaoAlertasService

router = APIRouter(prefix="/historico", tags=["historico-relatorios"])
service = GestaoAlertasService()


@router.get("", response_model=list[ReconhecimentoRegistrado])
def historico(zona_id: str | None = None, usuario: str | None = None):
    return service.historico(zona_id=zona_id, usuario=usuario)


@router.get("/relatorio/{zona_id}")
def relatorio_por_zona(zona_id: str):
    return service.relatorio_por_zona(zona_id)
