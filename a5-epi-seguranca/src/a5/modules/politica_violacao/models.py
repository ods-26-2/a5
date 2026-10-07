from pydantic import BaseModel, Field


class PoliticaViolacao(BaseModel):
    id: str
    zona_id: str
    epi_id: str
    tempo_tolerancia_segundos: int = Field(..., ge=0)
    confianca_minima: float = Field(..., ge=0.0, le=1.0)


class NovaPolitica(BaseModel):
    zona_id: str
    epi_id: str
    tempo_tolerancia_segundos: int = Field(..., ge=0)
    confianca_minima: float = Field(..., ge=0.0, le=1.0)


class Turno(BaseModel):
    """RF12 - horarios de monitoramento ativo por zona."""
    zona_id: str
    inicio: str  # "HH:MM"
    fim: str  # "HH:MM"
