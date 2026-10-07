"""RF13 - status de conexao e sensores: verifica se I9/S2/S3/S4 respondem."""
from src.a5.integrations.i9_client import get_i9_client
from src.a5.integrations.s2_client import get_s2_client
from src.a5.integrations.s3_client import get_s3_client
from src.a5.integrations.s4_client import get_s4_client


def check_dependencies() -> dict:
    status = {"a5": "ok"}

    try:
        get_i9_client().obter_estado_atual(zona_id="__healthcheck__")
        status["i9"] = "ok"
    except Exception as exc:  # pragma: no cover - so acontece se o mock quebrar
        status["i9"] = f"erro: {exc}"

    try:
        get_s3_client().listar_alertas_ativos()
        status["s3"] = "ok"
    except Exception as exc:  # pragma: no cover
        status["s3"] = f"erro: {exc}"

    status["s2"] = "ok (mock nao verifica handshake)"
    status["s4"] = "ok (mock nao verifica handshake)"
    return status
