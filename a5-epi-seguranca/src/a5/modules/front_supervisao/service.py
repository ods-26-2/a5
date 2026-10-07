"""
Modulo Front de Supervisao.

RF7 - Exibir violacoes com evidencia (S4) e descricao especifica.
RF8 - Isolamento: este service e o UNICO ponto que o endpoint de supervisao chama;
      nunca expor I9/S2/S3/S4 diretamente para o front.
"""
from src.a5.integrations.s4_client import S4Client, get_s4_client
from src.a5.modules.front_supervisao.dto import OcorrenciaSupervisao
from src.a5.modules.gestao_alertas.service import GestaoAlertasService


class FrontSupervisaoService:
    def __init__(
        self,
        gestao_alertas: GestaoAlertasService | None = None,
        s4_client: S4Client | None = None,
    ):
        self._gestao_alertas = gestao_alertas or GestaoAlertasService()
        self._s4 = s4_client or get_s4_client()

    def listar_ocorrencias(self, zona_id: str | None = None) -> list[OcorrenciaSupervisao]:
        alertas = self._gestao_alertas.alertas_ativos(zona_id)
        ocorrencias = []
        for a in alertas:
            evidencia = self._s4.obter_evidencia(a.alerta_id)
            ocorrencias.append(
                OcorrenciaSupervisao(
                    alerta_id=a.alerta_id,
                    zona_id=a.zona_id,
                    pessoa_id=a.pessoa_id,
                    epi=a.epi,
                    severidade=a.severidade,
                    descricao=(
                        f"EPI '{a.epi}' em desconformidade para a pessoa "
                        f"'{a.pessoa_id}' na zona '{a.zona_id}'."
                    ),
                    evidencia_url=evidencia.url_referencia if evidencia else None,
                )
            )
        return ocorrencias
