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


def test_historico_filtra_por_zona_tipo_e_periodo():
    from datetime import datetime, timedelta, timezone

    service = _service()
    a1, a2 = service.alertas_ativos("zona-producao-1")[0], service.alertas_ativos("zona-solda-2")[0]
    service.reconhecer(a1.alerta_id, "supervisor.joana")
    service.silenciar(a2.alerta_id, "supervisor.joana")

    # RF11: filtro por setor (antes o zona_id era aceito e ignorado)
    assert [r.alerta_id for r in service.historico(zona_id="zona-producao-1")] == [a1.alerta_id]
    assert [r.alerta_id for r in service.historico(zona_id="zona-solda-2")] == [a2.alerta_id]
    assert [r.tipo for r in service.historico(tipo="mute")] == ["mute"]
    assert service.historico(zona_id="zona-producao-1")[0].epi == "capacete"

    agora = datetime.now(timezone.utc)
    assert len(service.historico(desde=agora - timedelta(minutes=1))) == 2
    assert service.historico(desde=agora + timedelta(minutes=1)) == []
    # data sem fuso (como chega pela query string) e tratada como UTC, sem erro
    assert len(service.historico(ate=(agora + timedelta(minutes=1)).replace(tzinfo=None))) == 2


def test_relatorio_por_zona_tem_por_epi_e_respeita_periodo():
    from datetime import datetime, timezone

    service = _service()
    r = service.relatorio_por_zona("zona-producao-1")
    assert r["total"] == 1 and r["por_epi"] == {"capacete": 1} and r["por_severidade"] == {"alta": 1}
    # alertas do mock sao de 23/09/2026: periodo posterior nao os inclui
    vazio = service.relatorio_por_zona("zona-producao-1", desde=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert vazio["total"] == 0 and vazio["por_epi"] == {}


def test_alerta_traz_deteccoes_e_s4_so_o_descritor_do_clipe():
    from src.a5.integrations.s4_client import S4ClientMock

    alerta = _service().alertas_ativos("zona-producao-1")[0]
    assert alerta.deteccoes and 0 <= alerta.deteccoes[0].x <= 1
    evidencia = S4ClientMock().obter_evidencia(alerta.alerta_id)
    assert evidencia.inicio_seg is not None and evidencia.fim_seg is not None
    assert not hasattr(evidencia, "deteccoes")
