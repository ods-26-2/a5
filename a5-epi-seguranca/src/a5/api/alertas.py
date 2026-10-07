"""RF3, RF4, RF5, RF6 - estado, alertas ativos, ACK, MUTE e desligamento manual."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.a5.auth.permissions import Papel
from src.a5.integrations.i9_client import EstadoItemEPI
from src.a5.integrations.s3_client import AlertaS3
from src.a5.modules.gestao_alertas.models import RegistroDesligamento
from src.a5.modules.gestao_alertas.service import GestaoAlertasService

router = APIRouter(prefix="/alertas", tags=["gestao-alertas"])
service = GestaoAlertasService()


class AcaoAlerta(BaseModel):
    usuario: str


class DesligamentoRequest(BaseModel):
    usuario: str
    papel: Papel
    motivo: str | None = None


@router.get("/zonas/{zona_id}/estado", response_model=list[EstadoItemEPI])
def estado_atual(zona_id: str):
    return service.estado_atual_da_zona(zona_id)


@router.get("", response_model=list[AlertaS3])
def alertas_ativos(zona_id: str | None = None):
    return service.alertas_ativos(zona_id)


@router.post("/{alerta_id}/ack")
def reconhecer(alerta_id: str, acao: AcaoAlerta):
    if not service.reconhecer(alerta_id, acao.usuario):
        raise HTTPException(status_code=400, detail="Falha ao registrar ACK.")
    return {"status": "reconhecido"}


@router.post("/{alerta_id}/mute")
def silenciar(alerta_id: str, acao: AcaoAlerta):
    if not service.silenciar(alerta_id, acao.usuario):
        raise HTTPException(status_code=400, detail="Falha ao silenciar.")
    return {"status": "silenciado"}


@router.post("/{alerta_id}/desligar", response_model=RegistroDesligamento)
def desligar(alerta_id: str, req: DesligamentoRequest):
    try:
        return service.desligar_manualmente(alerta_id, req.usuario, req.papel, req.motivo)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
