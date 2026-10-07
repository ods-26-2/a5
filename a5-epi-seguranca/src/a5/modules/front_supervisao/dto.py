from pydantic import BaseModel


class OcorrenciaSupervisao(BaseModel):
    """O que o painel de supervisao (RF7) exibe: alerta + evidencia + descricao."""
    alerta_id: str
    zona_id: str
    pessoa_id: str
    epi: str
    severidade: str
    descricao: str
    evidencia_url: str | None
