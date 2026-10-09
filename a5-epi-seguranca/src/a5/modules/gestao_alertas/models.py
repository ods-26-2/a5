from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.a5.integrations.i9_client import EstadoItemEPI


class RegistroDesligamento(BaseModel):
    alerta_id: str
    usuario: str
    registrado_em: datetime
    motivo: str | None = None


class ReconhecimentoRegistrado(BaseModel):
    alerta_id: str
    usuario: str
    registrado_em: datetime
    tipo: str  # "ack" | "mute" | "desligamento"
    zona_id: str | None = None  # contexto do alerta no momento da acao (RF11: filtro por setor)
    epi: str | None = None
    # Evidencia do alerta no momento da acao (S4), para a auditoria rever o que foi tratado.
    evidencia_url: str | None = None
    evidencia_inicio_seg: float | None = None
    evidencia_fim_seg: float | None = None


class EstadoClassificado(EstadoItemEPI):
    """Estado do I9 + faixa de confianca (RNF2). 'incerta' = duvida."""
    classificacao: Literal["baixa", "incerta", "alta"]
