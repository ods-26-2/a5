"""Cadastro de zonas monitoradas. Alterar a geometria de uma zona com politica
gera automaticamente uma nova versao da politica (e reenvia ao S2)."""
from fastapi import APIRouter, Depends, HTTPException

from src.a5.auth.deps import exigir_login, pode_configurar
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.gestao_alertas.service import GestaoAlertasService
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService
from src.a5.modules.zonas.models import AtualizarZona, NovaZona, ZonaCadastro
from src.a5.modules.zonas.service import ZonaService

router = APIRouter(prefix="/zonas", tags=["zonas"])
service = ZonaService()
politicas = PoliticaViolacaoService()
historico = GestaoAlertasService()
catalogo = CatalogoEPIService()


@router.get("", response_model=list[ZonaCadastro])
def listar_zonas(incluir_inativas: bool = False, _=Depends(exigir_login)):
    return service.listar(incluir_inativas)


@router.post("", response_model=ZonaCadastro, status_code=201)
def criar_zona(nova: NovaZona, _=Depends(pode_configurar)):
    try:
        return service.criar(nova)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{zona_id}", response_model=ZonaCadastro)
def obter_zona(zona_id: str, _=Depends(exigir_login)):
    zona = service.obter(zona_id)
    if zona is None:
        raise HTTPException(status_code=404, detail="Zona nao encontrada.")
    return zona


@router.put("/{zona_id}", response_model=ZonaCadastro)
def atualizar_zona(zona_id: str, dados: AtualizarZona, _=Depends(pode_configurar)):
    try:
        zona = service.atualizar(zona_id, dados)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if zona.ativa:
        politicas.reaplicar_zona(zona)
    return zona


@router.delete("/{zona_id}")
def remover_zona(zona_id: str, definitivo: bool = False, _=Depends(pode_configurar)):
    """Sem `definitivo`: desativa (a zona some da lista e nao aceita novas politicas; versoes e
    historico continuam). Com `definitivo=true`: apaga o cadastro, mas so se a zona nunca teve
    politica nem acao registrada, porque a auditoria (RNF1) referencia o id da zona."""
    zona = service.obter(zona_id)
    if zona is None:
        raise HTTPException(status_code=404, detail=f"Zona '{zona_id}' nao encontrada.")
    if not definitivo:
        return service.desativar(zona_id)
    if politicas.listar_versoes(zona_id):
        raise HTTPException(status_code=409, detail="A zona tem politica (versoes guardadas): desative em vez de apagar.")
    if historico.historico(zona_id=zona_id):
        raise HTTPException(status_code=409, detail="A zona tem acoes no historico de auditoria: desative em vez de apagar.")
    service.apagar(zona_id)
    politicas.substituir_turnos(zona_id, [])
    catalogo.sincronizar_zona(zona_id, [])
    return {"status": "apagada", "zona_id": zona_id}
