"""
Cliente para o S2 (Regras temporais e eventos - Camada 3, squad VER-6).

Contrato assumido (RF2): A5 envia os parametros da politica de violacao
(EPI, tempo, confianca minima, zona) para S2; S2 aplica persistencia minima
e limiar de confianca e, se a violacao for confirmada, repassa para S3 (o A5
nao fala com S2 para receber - so para configurar).
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel


class ParametrosViolacao(BaseModel):
    epi: str
    zona_id: str
    tempo_tolerancia_segundos: int
    confianca_minima: float


class S2Client(ABC):
    @abstractmethod
    def enviar_politica(self, parametros: ParametrosViolacao) -> bool:
        """Envia/atualiza os parametros de violacao no S2. Retorna sucesso."""


class S2ClientMock(S2Client):
    def __init__(self):
        self._enviados: list[ParametrosViolacao] = []

    def enviar_politica(self, parametros: ParametrosViolacao) -> bool:
        # Simula o envio: so guarda em memoria para inspecao em teste/debug.
        self._enviados.append(parametros)
        return True


def get_s2_client() -> S2Client:
    # TODO: quando existir S2ClientReal (comando textual via B3), escolher aqui
    return S2ClientMock()
