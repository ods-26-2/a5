"""RF3, RF4, RF5, RF6 - estado, alertas ativos, ACK, MUTE e desligamento manual."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.a5.auth.deps import exigir_login
from src.a5.auth.models import Usuario
from src.a5.auth.permissions import Papel
from src.a5.integrations.s3_client import AlertaS3
from src.a5.modules.gestao_alertas.models import EstadoClassificado, RegistroDesligamento
from src.a5.modules.gestao_alertas.service import GestaoAlertasService
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/alertas", tags=["gestao-alertas"])
service = GestaoAlertasService()
politicas = PoliticaViolacaoService()


class AcaoAlerta(BaseModel):
    usuario: str | None = None  # ignorado quando ha login: vale o usuario da sessao


class DesligamentoRequest(BaseModel):
    usuario: str | None = None
    papel: Papel | None = None  # ignorado quando ha login: vale o papel da sessao
    motivo: str | None = None


def _autor(sessao: Usuario | None, usuario: str | None) -> str:
    nome = sessao.id if sessao else usuario
    if not nome:
        raise HTTPException(status_code=422, detail="Informe o usuario (ou faca login).")
    return nome


@router.get("/zonas/{zona_id}/estado", response_model=list[EstadoClassificado])
def estado_atual(zona_id: str, _=Depends(exigir_login)):
    """Estado por item (I9) com a faixa de confianca (RNF2): baixa | incerta | alta.
    'incerta' = duvida: o painel mostra, mas nao vira acao automatica."""
    return [
        EstadoClassificado(**e.model_dump(), classificacao=politicas.classificar_confianca(e.confianca))
        for e in service.estado_atual_da_zona(zona_id)
    ]


@router.get("", response_model=list[AlertaS3])
def alertas_ativos(zona_id: str | None = None, _=Depends(exigir_login)):
    return service.alertas_ativos(zona_id)


@router.post("/{alerta_id}/ack")
def reconhecer(alerta_id: str, acao: AcaoAlerta, sessao=Depends(exigir_login)):
    if not service.reconhecer(alerta_id, _autor(sessao, acao.usuario)):
        raise HTTPException(status_code=400, detail="Falha ao registrar ACK.")
    return {"status": "reconhecido"}


@router.post("/{alerta_id}/mute")
def silenciar(alerta_id: str, acao: AcaoAlerta, sessao=Depends(exigir_login)):
    if not service.silenciar(alerta_id, _autor(sessao, acao.usuario)):
        raise HTTPException(status_code=400, detail="Falha ao silenciar.")
    return {"status": "silenciado"}


@router.post("/{alerta_id}/desligar", response_model=RegistroDesligamento)
def desligar(alerta_id: str, req: DesligamentoRequest, sessao=Depends(exigir_login)):
    papel = sessao.papel if sessao else req.papel
    if papel is None:
        raise HTTPException(status_code=422, detail="Informe o papel (ou faca login).")
    try:
        return service.desligar_manualmente(alerta_id, _autor(sessao, req.usuario), papel, req.motivo)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
