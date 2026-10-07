"""
Cliente para o S4 (Evidencia de midia - Camada 3, modulo compartilhado MOD-2).

Contrato assumido (RF7): A5 pede o descritor de clipe/imagem associado a um
alerta; midia trafega por referencia (URL/id), nunca embutida no evento.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel


class EvidenciaS4(BaseModel):
    alerta_id: str
    tipo: str  # "imagem" | "clipe"
    url_referencia: str
    inicio_seg: float | None = None
    fim_seg: float | None = None


class S4Client(ABC):
    @abstractmethod
    def obter_evidencia(self, alerta_id: str) -> EvidenciaS4 | None:
        ...


class S4ClientMock(S4Client):
    def obter_evidencia(self, alerta_id: str) -> EvidenciaS4 | None:
        # Mock fixo: qualquer alerta devolve uma "evidencia" de exemplo.
        return EvidenciaS4(
            alerta_id=alerta_id,
            tipo="clipe",
            url_referencia=f"https://s4.mock.local/evidencias/{alerta_id}.mp4",
            inicio_seg=0.0,
            fim_seg=6.0,
        )


def get_s4_client() -> S4Client:
    # TODO: quando existir S4ClientReal (request/reply via B3), escolher aqui
    return S4ClientMock()
