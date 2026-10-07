"""Persistencia em memoria. Trocar por um repositorio real (SQL) quando houver DB."""
from itertools import count
from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI

_EPIS_SEED = [
    EPI(id="capacete", nome="Capacete"),
    EPI(id="luvas", nome="Luvas"),
    EPI(id="oculos", nome="Oculos de protecao"),
    EPI(id="mascara", nome="Mascara"),
    EPI(id="protetor_auricular", nome="Protetor auricular"),
    EPI(id="bota", nome="Bota de seguranca"),
]


class CatalogoRepository:
    def __init__(self):
        self._epis: dict[str, EPI] = {e.id: e for e in _EPIS_SEED}
        self._entradas: dict[str, CatalogoEntrada] = {}
        self._ids = count(1)

    def listar_epis(self) -> list[EPI]:
        return list(self._epis.values())

    def listar_por_zona(self, zona_id: str) -> list[CatalogoEntrada]:
        return [e for e in self._entradas.values() if e.zona_id == zona_id and e.ativo]

    def adicionar(self, zona_id: str, epi_id: str) -> CatalogoEntrada:
        entrada = CatalogoEntrada(id=str(next(self._ids)), zona_id=zona_id, epi_id=epi_id)
        self._entradas[entrada.id] = entrada
        return entrada

    def desativar(self, entrada_id: str) -> bool:
        entrada = self._entradas.get(entrada_id)
        if not entrada:
            return False
        entrada.ativo = False
        return True


_repo_singleton = CatalogoRepository()


def get_catalogo_repository() -> CatalogoRepository:
    return _repo_singleton
