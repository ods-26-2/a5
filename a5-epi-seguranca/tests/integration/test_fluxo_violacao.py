"""
Fluxo ponta-a-ponta usando os mocks: cadastra EPI, define politica, consulta
estado (I9 mock), consulta alertas (S3 mock), reconhece e desliga.
Cobre RF1-RF8 no nivel de integracao entre os 4 modulos do A5.
"""
from src.a5.auth.permissions import Papel
from src.a5.modules.catalogo_epi.repository import CatalogoRepository
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.front_supervisao.service import FrontSupervisaoService
from src.a5.modules.gestao_alertas.service import GestaoAlertasService
from src.a5.modules.politica_violacao.models import NovaPolitica
from src.a5.modules.politica_violacao.repository import PoliticaRepository
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService


def test_fluxo_completo_com_mocks():
    catalogo_repo = CatalogoRepository()
    catalogo = CatalogoEPIService(repo=catalogo_repo)

    politica = PoliticaViolacaoService(repo=PoliticaRepository(), catalogo_service=catalogo)
    politica.definir_politica(
        NovaPolitica(
            zona={"id": "zona-producao-1", "nome": "Producao 1"},
            equipamentos_obrigatorios=["capacete", "luvas"],
            tempo_tolerancia_segundos=15,
            confianca_minima=0.5,
        )
    )
    assert catalogo.epi_exigido_na_zona("zona-producao-1", "capacete")

    gestao = GestaoAlertasService()
    estados = gestao.estado_atual_da_zona("zona-producao-1")
    assert any(e.epi == "capacete" and e.estado == "ausente" for e in estados)

    alertas = gestao.alertas_ativos("zona-producao-1")
    assert len(alertas) >= 1

    supervisao = FrontSupervisaoService(gestao_alertas=gestao)
    ocorrencias = supervisao.listar_ocorrencias("zona-producao-1")
    assert len(ocorrencias) == len(alertas)
    assert all(o.evidencia_url for o in ocorrencias)
    assert all(o.deteccoes for o in ocorrencias)  # vem do alerta (S3), nao do S4

    alerta_id = alertas[0].alerta_id
    assert gestao.reconhecer(alerta_id, "supervisor.joana") is True
    registro = gestao.desligar_manualmente(alerta_id, "supervisor.joana", Papel.SUPERVISOR)
    assert registro.alerta_id == alerta_id
