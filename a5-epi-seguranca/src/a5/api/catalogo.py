"""RF1 - Catalogo de EPIs exigidos por zona (espelho da politica quando a zona tem uma)."""
from fastapi import APIRouter, Depends, HTTPException

from src.a5.auth.deps import exigir_login, pode_configurar, somente_administrador

from src.a5.modules.catalogo_epi.models import (
    AtualizarEPI,
    CatalogoEntrada,
    EPI,
    NovaEntradaCatalogo,
    NovoEPI,
)
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

router = APIRouter(prefix="/catalogo", tags=["catalogo-epi"])
service = CatalogoEPIService()
politicas = PoliticaViolacaoService()


def _exigir_zona_sem_politica(zona_id: str | None) -> None:
    """Zona com politica tem os EPIs definidos por ela (uma politica por zona)."""
    if zona_id and politicas.politica_vigente(zona_id):
        raise HTTPException(
            status_code=409,
            detail=f"A zona '{zona_id}' tem politica: altere os equipamentos salvando uma nova versao dela.",
        )


@router.get("/epis", response_model=list[EPI])
def listar_epis_disponiveis(incluir_inativos: bool = True, _=Depends(exigir_login)):
    epis = service.listar_epis_disponiveis()
    return epis if incluir_inativos else [e for e in epis if e.ativo]


def _zonas_que_exigem(epi_id: str) -> list[str]:
    return [p.zona.id for p in politicas.listar_vigentes()
            if any(e.epi_id == epi_id for e in p.equipamentos_obrigatorios)]


@router.post("/epis", response_model=EPI, status_code=201)
def criar_epi(novo: NovoEPI, _=Depends(somente_administrador)):
    try:
        return service.criar_epi(novo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/epis/{epi_id}", response_model=EPI)
def atualizar_epi(epi_id: str, dados: AtualizarEPI, _=Depends(somente_administrador)):
    """Nome, aliases e ativo. Desativar um EPI exigido por politica vigente responde 409."""
    if dados.ativo is False and (zonas := _zonas_que_exigem(epi_id)):
        raise HTTPException(
            status_code=409,
            detail=f"O EPI '{epi_id}' e exigido pelas politicas das zonas: {', '.join(zonas)}.",
        )
    try:
        return service.atualizar_epi(epi_id, dados)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/epis/{epi_id}", response_model=EPI)
def desativar_epi(epi_id: str, _=Depends(somente_administrador)):
    return atualizar_epi(epi_id, AtualizarEPI(ativo=False))


@router.get("/zonas/{zona_id}", response_model=list[CatalogoEntrada])
def listar_exigidos_na_zona(zona_id: str, _=Depends(exigir_login)):
    return service.listar_exigidos_na_zona(zona_id)


@router.post("/zonas/{zona_id}", response_model=CatalogoEntrada)
def cadastrar_entrada(zona_id: str, entrada: NovaEntradaCatalogo, _=Depends(pode_configurar)):
    entrada.zona_id = zona_id
    _exigir_zona_sem_politica(zona_id)
    try:
        return service.cadastrar(entrada)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/entradas/{entrada_id}")
def desativar_entrada(entrada_id: str, _=Depends(pode_configurar)):
    _exigir_zona_sem_politica(service.zona_da_entrada(entrada_id))
    if not service.desativar(entrada_id):
        raise HTTPException(status_code=404, detail="Entrada nao encontrada.")
    return {"status": "desativada"}
