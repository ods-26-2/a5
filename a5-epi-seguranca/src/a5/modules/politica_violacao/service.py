"""
Modulo Politica de Violacao.

RF2  - Definir politica de violacao: uma politica por zona, versionada, com os
       equipamentos obrigatorios (tempo e confianca por equipamento); repassa a S2.
RF12 - Configurar turnos de monitoramento ativo por zona.
RNF2 - Confianca na faixa intermediaria nunca vira acao automatica nem silencio;
       aqui e onde a faixa e definida (ver config.settings).
"""
from datetime import datetime, timezone

from src.a5.config import settings
from src.a5.integrations.s2_client import (
    PoliticaS2,
    RequisitoS2,
    S2Client,
    ZonaS2,
    get_s2_client,
)
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.politica_violacao.models import (
    EquipamentoExigido,
    NovaPolitica,
    PoliticaViolacao,
    Turno,
    Zona,
)
from src.a5.modules.zonas.models import ZonaCadastro
from src.a5.modules.zonas.service import ZonaService
from src.a5.modules.politica_violacao.repository import PoliticaRepository, get_politica_repository


class PoliticaViolacaoService:
    def __init__(
        self,
        repo: PoliticaRepository | None = None,
        s2_client: S2Client | None = None,
        catalogo_service: CatalogoEPIService | None = None,
        zona_service: ZonaService | None = None,
    ):
        self._repo = repo or get_politica_repository()
        self._s2 = s2_client or get_s2_client()
        self._catalogo = catalogo_service or CatalogoEPIService()
        self._zonas = zona_service or ZonaService()

    def definir_politica(self, nova: NovaPolitica) -> PoliticaViolacao:
        """Cria a proxima versao da politica da zona e a envia ao S2."""
        equipamentos = self._resolver_equipamentos(nova.equipamentos_obrigatorios)
        # A zona vem do cadastro (criada na hora se ainda nao existir); a politica
        # guarda um retrato dela nesta versao.
        cadastro = self._zonas.upsert_da_politica(
            nova.zona.id, nova.zona.nome, nova.zona.poligono
        )
        nova = nova.model_copy(update={"zona": self._retrato(cadastro)})

        politica_id = nova.id or f"politica-{nova.zona.id}"
        dona = self._repo.zona_da_politica(politica_id)
        if dona is not None and dona != nova.zona.id:
            raise ValueError(f"O id '{politica_id}' ja pertence a politica da zona '{dona}'.")

        politica = PoliticaViolacao(
            id=politica_id,
            versao=self._repo.proxima_versao(politica_id),
            zona=nova.zona,
            classe_pessoa=nova.classe_pessoa,
            equipamentos_obrigatorios=equipamentos,
            tempo_tolerancia_segundos=nova.tempo_tolerancia_segundos,
            confianca_minima=nova.confianca_minima,
            criada_em=datetime.now(timezone.utc),
        )
        self._repo.salvar(politica)

        # O catalogo da zona (RF1) passa a refletir o que a politica exige.
        self._catalogo.sincronizar_zona(politica.zona.id, [e.epi_id for e in equipamentos])

        self._s2.enviar_politica(self.montar_documento_s2(politica))
        return politica

    @staticmethod
    def _retrato(zona: ZonaCadastro) -> Zona:
        return Zona(id=zona.id, nome=zona.nome, poligono=zona.poligono)

    def reaplicar_zona(self, zona: ZonaCadastro) -> PoliticaViolacao | None:
        """Zona alterada no cadastro: se a politica vigente guarda outro retrato,
        cria nova versao com os mesmos equipamentos e reenvia ao S2."""
        vigente = self._repo.vigente(zona.id)
        if vigente is None or vigente.zona == self._retrato(zona):
            return None
        return self.definir_politica(
            NovaPolitica(
                id=vigente.id,
                zona=self._retrato(zona),
                classe_pessoa=vigente.classe_pessoa,
                equipamentos_obrigatorios=vigente.equipamentos_obrigatorios,
                tempo_tolerancia_segundos=vigente.tempo_tolerancia_segundos,
                confianca_minima=vigente.confianca_minima,
            )
        )

    def _resolver_equipamentos(self, itens: list[EquipamentoExigido]) -> list[EquipamentoExigido]:
        """Troca alias/nome pelo id canonico e recusa EPI desconhecido ou repetido."""
        resolvidos: list[EquipamentoExigido] = []
        vistos: set[str] = set()
        for item in itens:
            epi_id = self._catalogo.resolver_epi(item.epi_id)
            if epi_id is None:
                raise ValueError(f"EPI '{item.epi_id}' nao existe no catalogo global.")
            if epi_id in vistos:
                raise ValueError(f"EPI '{epi_id}' aparece mais de uma vez na politica.")
            vistos.add(epi_id)
            resolvidos.append(item.model_copy(update={"epi_id": epi_id}))
        return resolvidos

    def montar_documento_s2(self, politica: PoliticaViolacao) -> PoliticaS2:
        requisitos = politica.requisitos()
        return PoliticaS2(
            policy_id=politica.id,
            version=politica.versao,
            person_class=politica.classe_pessoa,
            zone=ZonaS2(
                id=politica.zona.id,
                name=politica.zona.nome,
                coordinate_space="image_normalized",
                polygon=[p.model_dump() for p in politica.zona.poligono],
            ),
            required_equipment=[
                RequisitoS2(
                    epi=r.epi_id,
                    tolerance_seconds=r.tempo_tolerancia_segundos,
                    min_confidence=r.confianca_minima,
                )
                for r in requisitos
            ],
            class_aliases={r.epi_id: self._catalogo.aliases_do_epi(r.epi_id) for r in requisitos},
        )

    def politica_vigente(self, zona_id: str) -> PoliticaViolacao | None:
        return self._repo.vigente(zona_id)

    def listar_versoes(self, zona_id: str) -> list[PoliticaViolacao]:
        return self._repo.versoes_da_zona(zona_id)

    def listar_vigentes(self) -> list[PoliticaViolacao]:
        return self._repo.listar_vigentes()

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

    def substituir_turnos(self, zona_id: str, turnos: list[Turno]) -> list[Turno]:
        """RF12 - troca a grade de turnos da zona de uma vez."""
        novos = [t.model_copy(update={"zona_id": zona_id}) for t in turnos]
        return self._repo.substituir_turnos(zona_id, novos)

    def monitoramento_ativo(self, zona_id: str, agora: datetime | None = None) -> bool:
        """RF12 - a zona esta em turno agora? Sem turnos cadastrados = sempre ativa.
        Turno que cruza a meia-noite (22:00-06:00) e tratado como um unico periodo."""
        turnos = self._repo.listar_turnos(zona_id)
        if not turnos:
            return True
        agora = agora or datetime.now()
        minuto = agora.hour * 60 + agora.minute
        for t in turnos:
            ini, fim = t.minutos()
            if (ini <= minuto < fim) if ini < fim else (minuto >= ini or minuto < fim):
                return True
        return False
