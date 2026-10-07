"""
Cliente para o I9 (Conformidade de uso relacional - Camada 2).

Contrato assumido (RF3): I9 expoe o estado por item de EPI para uma pessoa em
uma zona - correto / incorreto / ausente - com confianca por item. Ver
docs/contratos.md para o payload completo assumido.

Quando o I9 real existir (evento Pub/Sub via B3), criar `I9ClientReal` que
implementa `I9Client` e trocar em config.py / composicao de dependencias.
Nada no resto do A5 deve mudar.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

EstadoEPI = Literal["correto", "incorreto", "ausente"]

FIXTURES = Path(__file__).resolve().parent.parent / "mocks" / "fixtures" / "i9_estados.json"


class EstadoItemEPI(BaseModel):
    pessoa_id: str
    zona_id: str
    epi: str
    estado: EstadoEPI
    confianca: float


class I9Client(ABC):
    @abstractmethod
    def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]:
        """Retorna o estado por item de EPI para todas as pessoas na zona."""


class I9ClientMock(I9Client):
    """Le estados de exemplo de um fixture JSON, sem chamar nada de verdade."""

    def __init__(self, fixture_path: Path = FIXTURES):
        self._fixture_path = fixture_path

    def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]:
        dados = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        estados = [EstadoItemEPI(**item) for item in dados]
        return [e for e in estados if e.zona_id == zona_id]


def get_i9_client() -> I9Client:
    # TODO: quando existir I9ClientReal, escolher aqui com base em settings.i9_client
    return I9ClientMock()
