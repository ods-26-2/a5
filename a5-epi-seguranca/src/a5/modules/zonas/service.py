"""
Modulo Zonas.

Cadastro das zonas monitoradas (id, nome, camera, poligono). A politica de
violacao (RF2) referencia uma zona cadastrada e guarda um retrato dela a cada
versao. Quando o S1 publicar o contrato de zonas/cameras, este modulo e o ponto
de integracao.
"""
from datetime import datetime, timezone

from src.a5.modules.politica_violacao.models import Ponto
from src.a5.modules.zonas.models import AtualizarZona, NovaZona, ZonaCadastro
from src.a5.modules.zonas.repository import ZonaRepository, get_zona_repository


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class ZonaService:
    def __init__(self, repo: ZonaRepository | None = None):
        self._repo = repo or get_zona_repository()

    def listar(self, incluir_inativas: bool = False) -> list[ZonaCadastro]:
        return [z for z in self._repo.listar() if incluir_inativas or z.ativa]

    def obter(self, zona_id: str) -> ZonaCadastro | None:
        return self._repo.buscar(zona_id)

    def criar(self, nova: NovaZona) -> ZonaCadastro:
        existente = self._repo.buscar(nova.id)
        if existente:
            dica = " (esta desativada: reative-a em vez de criar outra)" if not existente.ativa else ""
            raise ValueError(f"A zona '{nova.id}' ja existe{dica}.")
        return self._repo.salvar(
            ZonaCadastro(**nova.model_dump(), atualizada_em=_agora())
        )

    def atualizar(self, zona_id: str, dados: AtualizarZona) -> ZonaCadastro:
        zona = self._repo.buscar(zona_id)
        if zona is None:
            raise LookupError(f"Zona '{zona_id}' nao encontrada.")
        campos = dados.model_dump(exclude_unset=True)
        campos = {k: v for k, v in campos.items() if v is not None or k in ("nome", "descricao", "camera_id")}
        if "poligono" in dados.model_fields_set and dados.poligono is not None:
            campos["poligono"] = dados.poligono
        novo = zona.model_copy(update={**campos, "atualizada_em": _agora()})
        return self._repo.salvar(novo)

    def apagar(self, zona_id: str) -> None:
        """Remove o cadastro de vez. Quem chama garante que nao ha politica nem historico."""
        if not self._repo.remover(zona_id):
            raise LookupError(f"Zona '{zona_id}' nao encontrada.")

    def desativar(self, zona_id: str) -> ZonaCadastro:
        return self.atualizar(zona_id, AtualizarZona(ativa=False))

    def upsert_da_politica(
        self, zona_id: str, nome: str | None, poligono: list[Ponto]
    ) -> ZonaCadastro:
        """Politica enviada com a zona: cria a zona se nao existir; geometria/nome
        informados atualizam o cadastro, e campos vazios herdam o que ja esta salvo."""
        zona = self._repo.buscar(zona_id)
        if zona is None:
            return self._repo.salvar(
                ZonaCadastro(id=zona_id, nome=nome, poligono=poligono, atualizada_em=_agora())
            )
        if not zona.ativa:
            raise ValueError(f"A zona '{zona_id}' esta desativada.")
        mudancas: dict = {}
        if nome and nome != zona.nome:
            mudancas["nome"] = nome
        if poligono and poligono != zona.poligono:
            mudancas["poligono"] = poligono
        if not mudancas:
            return zona
        return self._repo.salvar(zona.model_copy(update={**mudancas, "atualizada_em": _agora()}))
