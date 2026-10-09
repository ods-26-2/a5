"""
Modulo Gestao de Alertas.

RF3  - Receber estado por item de I9 (via orquestracao simples abaixo).
RF4  - Disparar/consultar alertas de violacao roteados por S3.
RF5  - Reconhecimento (ACK) do alerta, com autor e horario.
RF6  - Desligamento manual do alarme por profissional competente, auditado.
RF10 - Relatorios analiticos de violacoes.
RF11 - Consulta de historico com filtros.
RNF1 - Toda ACK/MUTE/desligamento registra autor e horario.
"""
from datetime import datetime, timezone


def _utc(dt: datetime | None) -> datetime | None:
    """Datas sem fuso (vindas da query string) sao tratadas como UTC."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


from src.a5.auth.permissions import Papel, usuario_pode_desligar_alarme
from src.a5.integrations.i9_client import EstadoItemEPI, I9Client, get_i9_client
from src.a5.integrations.s3_client import AlertaS3, S3Client, get_s3_client
from src.a5.integrations.s4_client import S4Client, get_s4_client
from src.a5.modules.gestao_alertas.models import RegistroDesligamento, ReconhecimentoRegistrado
from src.a5.modules.gestao_alertas.repository import (
    GestaoAlertasRepository,
    get_gestao_alertas_repository,
)


class GestaoAlertasService:
    def __init__(
        self,
        repo: GestaoAlertasRepository | None = None,
        i9_client: I9Client | None = None,
        s3_client: S3Client | None = None,
        s4_client: S4Client | None = None,
    ):
        self._repo = repo or get_gestao_alertas_repository()
        self._i9 = i9_client or get_i9_client()
        self._s3 = s3_client or get_s3_client()
        self._s4 = s4_client or get_s4_client()

    def estado_atual_da_zona(self, zona_id: str) -> list[EstadoItemEPI]:
        """RF3 - estado por item vindo de I9."""
        return self._i9.obter_estado_atual(zona_id)

    def alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
        """RF4 - alertas qualificados vindos de S3."""
        return self._s3.listar_alertas_ativos(zona_id)

    def _contexto(self, alerta_id: str) -> dict:
        """Zona, EPI e evidencia do alerta, gravados junto da acao: a auditoria filtra por
        setor e consegue rever o que foi tratado mesmo depois do alerta sair da lista."""
        alerta = next((a for a in self._s3.listar_alertas_ativos() if a.alerta_id == alerta_id), None)
        if not alerta:
            return {}
        contexto = {"zona_id": alerta.zona_id, "epi": alerta.epi}
        evidencia = self._s4.obter_evidencia(alerta_id)
        if evidencia:
            contexto.update(
                evidencia_url=evidencia.url_referencia,
                evidencia_inicio_seg=evidencia.inicio_seg,
                evidencia_fim_seg=evidencia.fim_seg,
            )
        return contexto

    def reconhecer(self, alerta_id: str, usuario: str) -> bool:
        """RF5 - ACK."""
        ok = self._s3.enviar_ack(alerta_id, usuario)
        if ok:
            self._repo.registrar_acao(
                ReconhecimentoRegistrado(
                    alerta_id=alerta_id,
                    usuario=usuario,
                    registrado_em=datetime.now(timezone.utc),
                    tipo="ack",
                    **self._contexto(alerta_id),
                )
            )
        return ok

    def silenciar(self, alerta_id: str, usuario: str) -> bool:
        """MUTE - silenciamento temporario, distinto do desligamento (RF6)."""
        ok = self._s3.enviar_mute(alerta_id, usuario)
        if ok:
            self._repo.registrar_acao(
                ReconhecimentoRegistrado(
                    alerta_id=alerta_id,
                    usuario=usuario,
                    registrado_em=datetime.now(timezone.utc),
                    tipo="mute",
                    **self._contexto(alerta_id),
                )
            )
        return ok

    def desligar_manualmente(self, alerta_id: str, usuario: str, papel: Papel, motivo: str | None = None):
        """RF6 - restrito a profissional competente (RF9/permissoes)."""
        if not usuario_pode_desligar_alarme(papel):
            raise PermissionError(f"Papel '{papel}' nao pode desligar o alarme manualmente.")

        registro = RegistroDesligamento(
            alerta_id=alerta_id,
            usuario=usuario,
            registrado_em=datetime.now(timezone.utc),
            motivo=motivo,
        )
        self._repo.registrar_desligamento(registro)
        self._repo.registrar_acao(
            ReconhecimentoRegistrado(
                alerta_id=alerta_id,
                usuario=usuario,
                registrado_em=registro.registrado_em,
                tipo="desligamento",
                **self._contexto(alerta_id),
            )
        )
        return registro

    def historico(
        self,
        zona_id: str | None = None,
        usuario: str | None = None,
        tipo: str | None = None,
        desde: datetime | None = None,
        ate: datetime | None = None,
    ):
        """RF11 - consulta de historico com filtros (setor, usuario, tipo de acao, periodo)."""
        return self._repo.historico(
            zona_id=zona_id, usuario=usuario, tipo=tipo, desde=_utc(desde), ate=_utc(ate)
        )

    def relatorio_por_zona(
        self, zona_id: str, desde: datetime | None = None, ate: datetime | None = None
    ) -> dict:
        """RF10 - relatorio analitico: violacoes por severidade e por tipo de EPI, no periodo."""
        desde, ate = _utc(desde), _utc(ate)
        alertas = [
            a for a in self.alertas_ativos(zona_id)
            if (desde is None or a.criado_em >= desde) and (ate is None or a.criado_em <= ate)
        ]
        por_severidade: dict[str, int] = {}
        por_epi: dict[str, int] = {}
        for a in alertas:
            por_severidade[a.severidade] = por_severidade.get(a.severidade, 0) + 1
            por_epi[a.epi] = por_epi.get(a.epi, 0) + 1
        return {
            "zona_id": zona_id,
            "total": len(alertas),
            "por_severidade": por_severidade,
            "por_epi": por_epi,
        }
