"""
Cliente para o S3 (Alertas e notificacoes - Camada 3, tambem entregue pelo VER-3).

Contrato assumido: S3 envia alertas qualificados (severidade, canal, dados do
evento) para o A5; o A5 envia de volta comandos de ACK (reconhecimento) e MUTE
(silenciamento), distintos do desligamento manual completo (RF6), que e uma
decisao exclusiva do A5 registrada localmente.
"""
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Severidade = Literal["baixa", "media", "alta", "critica"]

FIXTURES = Path(__file__).resolve().parent.parent / "mocks" / "fixtures" / "s3_alertas.json"


class AlertaS3(BaseModel):
    alerta_id: str
    zona_id: str
    pessoa_id: str
    epi: str
    severidade: Severidade
    criado_em: datetime
    reconhecido: bool = False
    silenciado: bool = False


class S3Client(ABC):
    @abstractmethod
    def listar_alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
        ...

    @abstractmethod
    def enviar_ack(self, alerta_id: str, usuario: str) -> bool:
        """RF5 - reconhecimento do alerta."""

    @abstractmethod
    def enviar_mute(self, alerta_id: str, usuario: str) -> bool:
        """Silenciamento temporario, distinto do desligamento manual (RF6)."""


class S3ClientMock(S3Client):
    def __init__(self, fixture_path: Path = FIXTURES):
        self._fixture_path = fixture_path
        self._acks: dict[str, str] = {}
        self._mutes: dict[str, str] = {}

    def _carregar(self) -> list[AlertaS3]:
        dados = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        alertas = [AlertaS3(**item) for item in dados]
        for a in alertas:
            a.reconhecido = a.alerta_id in self._acks
            a.silenciado = a.alerta_id in self._mutes
        return alertas

    def listar_alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
        alertas = self._carregar()
        if zona_id:
            alertas = [a for a in alertas if a.zona_id == zona_id]
        return alertas

    def enviar_ack(self, alerta_id: str, usuario: str) -> bool:
        self._acks[alerta_id] = usuario
        return True

    def enviar_mute(self, alerta_id: str, usuario: str) -> bool:
        self._mutes[alerta_id] = usuario
        return True


def get_s3_client() -> S3Client:
    # TODO: quando existir S3ClientReal (Pub/Sub + comando via B3), escolher aqui
    return S3ClientMock()
