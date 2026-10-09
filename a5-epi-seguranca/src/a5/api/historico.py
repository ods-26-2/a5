"""RF10, RF11 - relatorios analiticos e historico com filtros (consulta e exportacao CSV)."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.a5.auth.deps import pode_ver_relatorios
from src.a5.modules.gestao_alertas.models import ReconhecimentoRegistrado
from src.a5.modules.gestao_alertas.service import GestaoAlertasService

router = APIRouter(prefix="/historico", tags=["historico-relatorios"])
service = GestaoAlertasService()

_COLUNAS = ["registrado_em", "tipo", "usuario", "alerta_id", "zona_id", "epi", "evidencia_url"]


def _csv(linhas: list[list], cabecalho: list[str], nome: str) -> Response:
    saida = io.StringIO()
    escritor = csv.writer(saida)
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return Response(
        # BOM para o Excel abrir acentos corretamente.
        content="﻿" + saida.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.get("", response_model=list[ReconhecimentoRegistrado])
def historico(
    zona_id: str | None = None,
    usuario: str | None = None,
    tipo: str | None = None,
    desde: datetime | None = None,
    ate: datetime | None = None,
    _=Depends(pode_ver_relatorios),
):
    """tipo: ack | mute | desligamento. desde/ate: ISO-8601 (sem fuso = UTC)."""
    return service.historico(zona_id=zona_id, usuario=usuario, tipo=tipo, desde=desde, ate=ate)


@router.get("/exportar")
def exportar_historico(
    zona_id: str | None = None,
    usuario: str | None = None,
    tipo: str | None = None,
    desde: datetime | None = None,
    ate: datetime | None = None,
    _=Depends(pode_ver_relatorios),
):
    """Mesmos filtros do historico, em CSV."""
    registros = service.historico(zona_id=zona_id, usuario=usuario, tipo=tipo, desde=desde, ate=ate)
    linhas = [
        [r.registrado_em.isoformat(), r.tipo, r.usuario, r.alerta_id, r.zona_id or "", r.epi or "", r.evidencia_url or ""]
        for r in registros
    ]
    return _csv(linhas, _COLUNAS, "historico-a5.csv")


@router.get("/relatorio/{zona_id}")
def relatorio_por_zona(
    zona_id: str,
    desde: datetime | None = None,
    ate: datetime | None = None,
    _=Depends(pode_ver_relatorios),
):
    return service.relatorio_por_zona(zona_id, desde=desde, ate=ate)


@router.get("/relatorio/{zona_id}/exportar")
def exportar_relatorio(
    zona_id: str,
    desde: datetime | None = None,
    ate: datetime | None = None,
    _=Depends(pode_ver_relatorios),
):
    rel = service.relatorio_por_zona(zona_id, desde=desde, ate=ate)
    linhas = [["total", "", rel["total"]]]
    linhas += [["severidade", k, v] for k, v in sorted(rel["por_severidade"].items())]
    linhas += [["epi", k, v] for k, v in sorted(rel["por_epi"].items())]
    return _csv(linhas, ["dimensao", "valor", "violacoes"], f"relatorio-{zona_id}.csv")
