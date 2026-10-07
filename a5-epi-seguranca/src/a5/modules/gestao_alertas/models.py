from datetime import datetime
from pydantic import BaseModel


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
