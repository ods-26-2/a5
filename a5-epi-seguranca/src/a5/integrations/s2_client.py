"""
Cliente para o S2 (Regras temporais e eventos - Camada 3, squad VER-6).

Contrato assumido (RF2): A5 envia a politica de violacao da zona (um documento
versionado: zona, classe de pessoa, equipamentos exigidos com tempo e confianca
minima, e os aliases de classe do detector) para S2; S2 aplica persistencia
minima e limiar de confianca e, se a violacao for confirmada, repassa para S3 (o
A5 nao fala com S2 para receber - so para configurar).
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class ZonaS2(BaseModel):
    id: str
    name: str | None = None
    coordinate_space: str = "image_normalized"  # V6/S1: zonas sempre declaram o espaco
    polygon: list[dict[str, float]] = Field(default_factory=list)  # [{"x":..,"y":..}] em [0,1]


class RequisitoS2(BaseModel):
    epi: str
    tolerance_seconds: int
    min_confidence: float


class PoliticaS2(BaseModel):
    policy_id: str
    version: int
    person_class: str
    zone: ZonaS2
    required_equipment: list[RequisitoS2]
    class_aliases: dict[str, list[str]]


class S2Client(ABC):
    @abstractmethod
    def enviar_politica(self, politica: PoliticaS2) -> bool:
        """Envia a nova versao da politica de uma zona ao S2. Retorna sucesso."""


class S2ClientMock(S2Client):
    def __init__(self):
        self._enviados: list[PoliticaS2] = []

    def enviar_politica(self, politica: PoliticaS2) -> bool:
        # Simula o envio: so guarda em memoria para inspecao em teste/debug.
        self._enviados.append(politica)
        return True


def get_s2_client() -> S2Client:
    # TODO: quando existir S2ClientReal (comando textual via B3), escolher aqui
    return S2ClientMock()
