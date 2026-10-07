"""Ponto de entrada do backend do A5 (FastAPI)."""
from fastapi import FastAPI

from src.a5.api import (
    acessos,
    alertas,
    catalogo,
    historico,
    monitoramento,
    politica,
    supervisao,
)

app = FastAPI(
    title="A5 · EPI - Segurança",
    description="Backend do componente A5 (Squad VER-3, ODS 2026/2 v6). "
    "Componentes I9, S2, S3 e S4 estao mockados em src/a5/integrations/.",
    version="0.1.0",
)

app.include_router(catalogo.router)
app.include_router(politica.router)
app.include_router(alertas.router)
app.include_router(supervisao.router)
app.include_router(historico.router)
app.include_router(acessos.router)
app.include_router(monitoramento.router)


@app.get("/health", tags=["saude"])
def health():
    """RF13 - status agregado do A5 e das dependencias externas mockadas."""
    from src.a5.integrations.health import check_dependencies

    return check_dependencies()
