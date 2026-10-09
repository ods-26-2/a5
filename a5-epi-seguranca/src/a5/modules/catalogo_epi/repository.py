"""Persistencia em memoria. Trocar por um repositorio real (SQL) quando houver DB."""
from itertools import count
from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI

_EPIS_SEED = [
    EPI(id="capacete", nome="Capacete", aliases=["capacete", "helmet", "hard hat"]),
    EPI(id="colete", nome="Colete refletivo", aliases=["colete", "vest", "safety vest"]),
    EPI(id="luvas", nome="Luvas", aliases=["luva", "luvas", "glove", "gloves"]),
    EPI(id="oculos", nome="Oculos de protecao", aliases=["oculos", "glasses", "goggles"]),
    EPI(id="mascara", nome="Mascara", aliases=["mascara", "mask"]),
    EPI(id="protetor_auricular", nome="Protetor auricular", aliases=["protetor auricular", "earmuffs"]),
    EPI(id="bota", nome="Bota de seguranca", aliases=["bota", "boot", "boots"]),
]


class CatalogoRepository:
    def __init__(self):
        self._epis: dict[str, EPI] = {e.id: e for e in _EPIS_SEED}
        self._entradas: dict[str, CatalogoEntrada] = {}
        self._ids = count(1)

    def listar_epis(self) -> list[EPI]:
        return list(self._epis.values())

    def buscar_epi(self, epi_id: str) -> EPI | None:
        return self._epis.get(epi_id)

    def salvar_epi(self, epi: EPI) -> EPI:
        self._epis[epi.id] = epi
        return epi

    def listar_por_zona(self, zona_id: str) -> list[CatalogoEntrada]:
        return [e for e in self._entradas.values() if e.zona_id == zona_id and e.ativo]

    def adicionar(self, zona_id: str, epi_id: str) -> CatalogoEntrada:
        entrada = CatalogoEntrada(id=str(next(self._ids)), zona_id=zona_id, epi_id=epi_id)
        self._entradas[entrada.id] = entrada
        return entrada

    def buscar_entrada(self, entrada_id: str) -> CatalogoEntrada | None:
        return self._entradas.get(entrada_id)

    def desativar(self, entrada_id: str) -> bool:
        entrada = self._entradas.get(entrada_id)
        if not entrada:
            return False
        entrada.ativo = False
        return True


_repo_singleton = CatalogoRepository()


def get_catalogo_repository() -> CatalogoRepository:
    return _repo_singleton
