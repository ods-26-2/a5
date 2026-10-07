from src.a5.auth.permissions import Papel
from src.a5.integrations.i9_client import I9ClientMock
from src.a5.integrations.s3_client import S3ClientMock
from src.a5.modules.gestao_alertas.repository import GestaoAlertasRepository
from src.a5.modules.gestao_alertas.service import GestaoAlertasService


def _service():
    return GestaoAlertasService(
        repo=GestaoAlertasRepository(), i9_client=I9ClientMock(), s3_client=S3ClientMock()
    )


def test_estado_atual_da_zona_usa_mock_i9():
    service = _service()
    estados = service.estado_atual_da_zona("zona-producao-1")
    assert len(estados) > 0
    assert all(e.zona_id == "zona-producao-1" for e in estados)


def test_reconhecer_alerta_registra_no_historico():
    service = _service()
    alertas = service.alertas_ativos()
    alerta_id = alertas[0].alerta_id
    assert service.reconhecer(alerta_id, "supervisor.joana") is True
    historico = service.historico(usuario="supervisor.joana")
    assert len(historico) == 1
    assert historico[0].tipo == "ack"


def test_desligamento_negado_para_operador():
    service = _service()
    alertas = service.alertas_ativos()
    try:
        service.desligar_manualmente(alertas[0].alerta_id, "operador.carlos", Papel.OPERADOR)
        assert False, "operador nao deveria poder desligar"
    except PermissionError:
        pass


def test_desligamento_permitido_para_supervisor():
    service = _service()
    alertas = service.alertas_ativos()
    registro = service.desligar_manualmente(
        alertas[0].alerta_id, "supervisor.joana", Papel.SUPERVISOR, motivo="situacao resolvida"
    )
    assert registro.usuario == "supervisor.joana"
