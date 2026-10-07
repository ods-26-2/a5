"""
Modulo Politica de Violacao.

RF2  - Definir politica de violacao (EPI, tempo, confianca, zona); repassa a S2.
RF12 - Configurar turnos de monitoramento ativo por zona.
RNF2 - Confianca na faixa intermediaria nunca vira acao automatica nem silencio;
       aqui e onde a faixa e definida (ver config.settings).
"""
from src.a5.config import settings
from src.a5.integrations.s2_client import ParametrosViolacao, S2Client, get_s2_client
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.politica_violacao.models import NovaPolitica, PoliticaViolacao, Turno
from src.a5.modules.politica_violacao.repository import PoliticaRepository, get_politica_repository


class PoliticaViolacaoService:
    def __init__(
        self,
        repo: PoliticaRepository | None = None,
        s2_client: S2Client | None = None,
        catalogo_service: CatalogoEPIService | None = None,
    ):
        self._repo = repo or get_politica_repository()
        self._s2 = s2_client or get_s2_client()
        self._catalogo = catalogo_service or CatalogoEPIService()

    def definir_politica(self, nova: NovaPolitica) -> PoliticaViolacao:
        # RF9 (parte): nao permite politica para EPI fora do catalogo ativo da zona.
        if not self._catalogo.epi_exigido_na_zona(nova.zona_id, nova.epi_id):
            raise ValueError(
                f"EPI '{nova.epi_id}' nao esta no catalogo ativo da zona '{nova.zona_id}'."
            )

        politica = PoliticaViolacao(id=self._repo.novo_id(), **nova.model_dump())
        self._repo.salvar(politica)

        # Repassa os parametros ao S2 (mockado por enquanto).
        self._s2.enviar_politica(
            ParametrosViolacao(
                epi=politica.epi_id,
                zona_id=politica.zona_id,
                tempo_tolerancia_segundos=politica.tempo_tolerancia_segundos,
                confianca_minima=politica.confianca_minima,
            )
        )
        return politica

    def listar_por_zona(self, zona_id: str) -> list[PoliticaViolacao]:
        return self._repo.listar_por_zona(zona_id)

    def classificar_confianca(self, confianca: float) -> str:
        """RNF2 - devolve 'baixa' | 'incerta' | 'alta' conforme a faixa configurada."""
        if confianca < settings.confianca_minima:
            return "baixa"
        if confianca > settings.confianca_maxima:
            return "alta"
        return "incerta"

    def definir_turno(self, turno: Turno) -> Turno:
        return self._repo.adicionar_turno(turno)

    def listar_turnos(self, zona_id: str) -> list[Turno]:
        return self._repo.listar_turnos(zona_id)
