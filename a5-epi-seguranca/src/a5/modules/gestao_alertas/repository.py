from datetime import datetime

from src.a5.modules.gestao_alertas.models import RegistroDesligamento, ReconhecimentoRegistrado


class GestaoAlertasRepository:
    """Historico local de acoes humanas sobre alertas (auditoria - RNF1)."""

    def __init__(self):
        self._desligamentos: list[RegistroDesligamento] = []
        self._registros: list[ReconhecimentoRegistrado] = []

    def registrar_acao(self, registro: ReconhecimentoRegistrado) -> None:
        self._registros.append(registro)

    def registrar_desligamento(self, registro: RegistroDesligamento) -> None:
        self._desligamentos.append(registro)

    def historico(
        self,
        zona_id: str | None = None,
        usuario: str | None = None,
        tipo: str | None = None,
        desde: datetime | None = None,
        ate: datetime | None = None,
    ) -> list[ReconhecimentoRegistrado]:
        registros = self._registros
        if zona_id:
            registros = [r for r in registros if r.zona_id == zona_id]
        if usuario:
            registros = [r for r in registros if r.usuario == usuario]
        if tipo:
            registros = [r for r in registros if r.tipo == tipo]
        if desde:
            registros = [r for r in registros if r.registrado_em >= desde]
        if ate:
            registros = [r for r in registros if r.registrado_em <= ate]
        return registros


_repo_singleton = GestaoAlertasRepository()


def get_gestao_alertas_repository() -> GestaoAlertasRepository:
    return _repo_singleton
