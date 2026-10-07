"""
Modulo Catalogo de EPI.

RF1  - Cadastrar catalogo de EPIs exigidos por area/setor.
RF9  - (parte) impedir configurar politica para EPI fora do catalogo ativo da zona.
"""
from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI, NovaEntradaCatalogo
from src.a5.modules.catalogo_epi.repository import CatalogoRepository, get_catalogo_repository


class CatalogoEPIService:
    def __init__(self, repo: CatalogoRepository | None = None):
        self._repo = repo or get_catalogo_repository()

    def listar_epis_disponiveis(self) -> list[EPI]:
        return self._repo.listar_epis()

    def listar_exigidos_na_zona(self, zona_id: str) -> list[CatalogoEntrada]:
        return self._repo.listar_por_zona(zona_id)

    def cadastrar(self, entrada: NovaEntradaCatalogo) -> CatalogoEntrada:
        epis_validos = {e.id for e in self._repo.listar_epis()}
        if entrada.epi_id not in epis_validos:
            raise ValueError(f"EPI '{entrada.epi_id}' nao existe no catalogo global.")
        return self._repo.adicionar(entrada.zona_id, entrada.epi_id)

    def desativar(self, entrada_id: str) -> bool:
        return self._repo.desativar(entrada_id)

    def epi_exigido_na_zona(self, zona_id: str, epi_id: str) -> bool:
        """Usado pela Politica de Violacao para validar consistencia (RF9)."""
        return any(e.epi_id == epi_id for e in self._repo.listar_por_zona(zona_id))
