"""Persistencia em memoria do cadastro de zonas."""
from src.a5.modules.zonas.models import ZonaCadastro


class ZonaRepository:
    def __init__(self):
        self._zonas: dict[str, ZonaCadastro] = {}

    def listar(self) -> list[ZonaCadastro]:
        return list(self._zonas.values())

    def buscar(self, zona_id: str) -> ZonaCadastro | None:
        return self._zonas.get(zona_id)

    def remover(self, zona_id: str) -> bool:
        return self._zonas.pop(zona_id, None) is not None

    def salvar(self, zona: ZonaCadastro) -> ZonaCadastro:
        self._zonas[zona.id] = zona
        return zona


_repo_singleton = ZonaRepository()


def get_zona_repository() -> ZonaRepository:
    return _repo_singleton
