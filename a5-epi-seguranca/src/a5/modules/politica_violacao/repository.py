from src.a5.modules.politica_violacao.models import PoliticaViolacao, Turno


class PoliticaRepository:
    """Guarda todas as versoes; a vigente de uma zona e a ultima salva para ela."""

    def __init__(self):
        self._versoes: list[PoliticaViolacao] = []  # ordem de gravacao
        self._turnos: list[Turno] = []

    def salvar(self, politica: PoliticaViolacao) -> PoliticaViolacao:
        self._versoes.append(politica)
        return politica

    def proxima_versao(self, politica_id: str) -> int:
        return 1 + max((p.versao for p in self._versoes if p.id == politica_id), default=0)

    def zona_da_politica(self, politica_id: str) -> str | None:
        return next((p.zona.id for p in self._versoes if p.id == politica_id), None)

    def vigente(self, zona_id: str) -> PoliticaViolacao | None:
        versoes = self.versoes_da_zona(zona_id)
        return versoes[-1] if versoes else None

    def versoes_da_zona(self, zona_id: str) -> list[PoliticaViolacao]:
        return [p for p in self._versoes if p.zona.id == zona_id]

    def listar_vigentes(self) -> list[PoliticaViolacao]:
        por_zona: dict[str, PoliticaViolacao] = {}
        for p in self._versoes:
            por_zona[p.zona.id] = p
        return list(por_zona.values())

    def adicionar_turno(self, turno: Turno) -> Turno:
        self._turnos.append(turno)
        return turno

    def substituir_turnos(self, zona_id: str, turnos: list[Turno]) -> list[Turno]:
        self._turnos = [t for t in self._turnos if t.zona_id != zona_id] + turnos
        return turnos

    def listar_turnos(self, zona_id: str) -> list[Turno]:
        return [t for t in self._turnos if t.zona_id == zona_id]


_repo_singleton = PoliticaRepository()


def get_politica_repository() -> PoliticaRepository:
    return _repo_singleton
