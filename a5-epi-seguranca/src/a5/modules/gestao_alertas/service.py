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

from src.a5.auth.permissions import Papel, usuario_pode_desligar_alarme
from src.a5.integrations.i9_client import EstadoItemEPI, I9Client, get_i9_client
from src.a5.integrations.s3_client import AlertaS3, S3Client, get_s3_client
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
    ):
        self._repo = repo or get_gestao_alertas_repository()
        self._i9 = i9_client or get_i9_client()
        self._s3 = s3_client or get_s3_client()

    def estado_atual_da_zona(self, zona_id: str) -> list[EstadoItemEPI]:
        """RF3 - estado por item vindo de I9."""
        return self._i9.obter_estado_atual(zona_id)

    def alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
        """RF4 - alertas qualificados vindos de S3."""
        return self._s3.listar_alertas_ativos(zona_id)

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
            )
        )
        return registro

    def historico(self, zona_id: str | None = None, usuario: str | None = None):
        """RF11 - consulta de historico com filtros."""
        return self._repo.historico(zona_id=zona_id, usuario=usuario)

    def relatorio_por_zona(self, zona_id: str) -> dict:
        """RF10 - relatorio analitico simples (contagem por severidade)."""
        alertas = self.alertas_ativos(zona_id)
        contagem: dict[str, int] = {}
        for a in alertas:
            contagem[a.severidade] = contagem.get(a.severidade, 0) + 1
        return {"zona_id": zona_id, "total": len(alertas), "por_severidade": contagem}
