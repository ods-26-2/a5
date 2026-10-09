from pydantic import BaseModel, Field

from src.a5.integrations.s3_client import Deteccao


class OcorrenciaSupervisao(BaseModel):
    """O que o painel de supervisao (RF7) exibe: alerta + evidencia + descricao."""
    alerta_id: str
    zona_id: str
    pessoa_id: str
    epi: str
    severidade: str
    descricao: str
    evidencia_url: str | None
    evidencia_inicio_seg: float | None = None
    evidencia_fim_seg: float | None = None
    em_violacao_ha_segundos: int | None = None  # RF7: ha quanto tempo a violacao dura
    deteccoes: list[Deteccao] = Field(default_factory=list)
