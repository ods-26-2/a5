"""
Modulo Catalogo de EPI.

RF1  - Cadastrar catalogo de EPIs exigidos por area/setor.
RF9  - (parte) impedir configurar politica para EPI fora do catalogo ativo da zona.
"""
import unicodedata

from src.a5.modules.catalogo_epi.models import (
    AtualizarEPI,
    CatalogoEntrada,
    EPI,
    NovaEntradaCatalogo,
    NovoEPI,
)
from src.a5.modules.catalogo_epi.repository import CatalogoRepository, get_catalogo_repository


def normalizar_nome(nome: str) -> str:
    """'CAPACETE', 'Capacete ' e 'capacête' viram a mesma chave."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.casefold().split())


class CatalogoEPIService:
    def __init__(self, repo: CatalogoRepository | None = None):
        self._repo = repo or get_catalogo_repository()

    def listar_epis_disponiveis(self) -> list[EPI]:
        return self._repo.listar_epis()

    def _nomes_de(self, epi: EPI) -> set[str]:
        return {normalizar_nome(n) for n in {epi.id, epi.nome, *epi.aliases}}

    def _checar_conflito(self, epi: EPI) -> None:
        """Nenhum nome/alias pode apontar para dois EPIs ao mesmo tempo."""
        meus = self._nomes_de(epi)
        for outro in self._repo.listar_epis():
            if outro.id != epi.id and meus & self._nomes_de(outro):
                comum = sorted(meus & self._nomes_de(outro))[0]
                raise ValueError(f"O nome/alias '{comum}' ja pertence ao EPI '{outro.id}'.")

    @staticmethod
    def _limpar_aliases(aliases: list[str]) -> list[str]:
        vistos: dict[str, str] = {}
        for a in aliases:
            a = " ".join(a.split())
            if a:
                vistos.setdefault(normalizar_nome(a), a)
        return list(vistos.values())

    def criar_epi(self, novo: NovoEPI) -> EPI:
        if self._repo.buscar_epi(novo.id):
            raise ValueError(f"O EPI '{novo.id}' ja existe.")
        epi = EPI(id=novo.id, nome=novo.nome.strip(), aliases=self._limpar_aliases(novo.aliases))
        self._checar_conflito(epi)
        return self._repo.salvar_epi(epi)

    def atualizar_epi(self, epi_id: str, dados: AtualizarEPI) -> EPI:
        atual = self._repo.buscar_epi(epi_id)
        if atual is None:
            raise LookupError(f"EPI '{epi_id}' nao encontrado.")
        campos = dados.model_dump(exclude_none=True)
        if "aliases" in campos:
            campos["aliases"] = self._limpar_aliases(campos["aliases"])
        if "nome" in campos:
            campos["nome"] = campos["nome"].strip()
        novo = atual.model_copy(update=campos)
        self._checar_conflito(novo)
        return self._repo.salvar_epi(novo)

    def listar_exigidos_na_zona(self, zona_id: str) -> list[CatalogoEntrada]:
        return self._repo.listar_por_zona(zona_id)

    def cadastrar(self, entrada: NovaEntradaCatalogo) -> CatalogoEntrada:
        epis_validos = {e.id for e in self._repo.listar_epis() if e.ativo}
        if entrada.epi_id not in epis_validos:
            raise ValueError(f"EPI '{entrada.epi_id}' nao existe no catalogo global.")
        return self._repo.adicionar(entrada.zona_id, entrada.epi_id)

    def desativar(self, entrada_id: str) -> bool:
        return self._repo.desativar(entrada_id)

    def zona_da_entrada(self, entrada_id: str) -> str | None:
        entrada = self._repo.buscar_entrada(entrada_id)
        return entrada.zona_id if entrada else None

    def epi_exigido_na_zona(self, zona_id: str, epi_id: str) -> bool:
        """Usado pela Politica de Violacao para validar consistencia (RF9)."""
        return any(e.epi_id == epi_id for e in self._repo.listar_por_zona(zona_id))

    def resolver_epi(self, nome: str) -> str | None:
        """Converte id, nome ou alias de classe do detector no id canonico do EPI."""
        chave = normalizar_nome(nome)
        for epi in self._repo.listar_epis():
            if not epi.ativo:
                continue
            nomes = {epi.id, epi.nome, *epi.aliases}
            if chave in {normalizar_nome(n) for n in nomes}:
                return epi.id
        return None

    def aliases_do_epi(self, epi_id: str) -> list[str]:
        epi = self._repo.buscar_epi(epi_id)
        return list(epi.aliases) if epi else []

    def sincronizar_zona(self, zona_id: str, epi_ids: list[str]) -> None:
        """Faz o catalogo ativo da zona refletir a politica vigente (RF1 x RF2)."""
        desejados = set(epi_ids)
        ativos = {e.epi_id: e for e in self._repo.listar_por_zona(zona_id)}
        for epi_id in desejados - ativos.keys():
            self._repo.adicionar(zona_id, epi_id)
        for epi_id, entrada in ativos.items():
            if epi_id not in desejados:
                self._repo.desativar(entrada.id)
