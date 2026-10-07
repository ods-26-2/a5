from itertools import count
from src.a5.modules.politica_violacao.models import PoliticaViolacao, Turno


class PoliticaRepository:
    def __init__(self):
        self._politicas: dict[str, PoliticaViolacao] = {}
        self._turnos: list[Turno] = []
        self._ids = count(1)

    def salvar(self, politica: PoliticaViolacao) -> PoliticaViolacao:
        self._politicas[politica.id] = politica
        return politica

    def novo_id(self) -> str:
        return str(next(self._ids))

    def listar_por_zona(self, zona_id: str) -> list[PoliticaViolacao]:
        return [p for p in self._politicas.values() if p.zona_id == zona_id]

    def adicionar_turno(self, turno: Turno) -> Turno:
        self._turnos.append(turno)
        return turno

    def listar_turnos(self, zona_id: str) -> list[Turno]:
        return [t for t in self._turnos if t.zona_id == zona_id]


_repo_singleton = PoliticaRepository()


def get_politica_repository() -> PoliticaRepository:
    return _repo_singleton
