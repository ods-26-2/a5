from src.a5.integrations.s2_client import S2ClientMock
from src.a5.modules.catalogo_epi.models import NovaEntradaCatalogo
from src.a5.modules.catalogo_epi.repository import CatalogoRepository
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.politica_violacao.models import NovaPolitica
from src.a5.modules.politica_violacao.repository import PoliticaRepository
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService


def _service_com_catalogo_preenchido():
    catalogo_repo = CatalogoRepository()
    catalogo_service = CatalogoEPIService(repo=catalogo_repo)
    catalogo_service.cadastrar(NovaEntradaCatalogo(zona_id="zona-1", epi_id="capacete"))
    s2 = S2ClientMock()
    service = PoliticaViolacaoService(
        repo=PoliticaRepository(), s2_client=s2, catalogo_service=catalogo_service
    )
    return service, s2


def test_definir_politica_envia_para_s2():
    service, s2 = _service_com_catalogo_preenchido()
    politica = service.definir_politica(
        NovaPolitica(zona_id="zona-1", epi_id="capacete", tempo_tolerancia_segundos=10, confianca_minima=0.7)
    )
    assert politica.zona_id == "zona-1"
    assert len(s2._enviados) == 1


def test_definir_politica_para_epi_fora_do_catalogo_falha():
    service, _ = _service_com_catalogo_preenchido()
    try:
        service.definir_politica(
            NovaPolitica(zona_id="zona-1", epi_id="oculos", tempo_tolerancia_segundos=5, confianca_minima=0.5)
        )
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


def test_classificar_confianca():
    service, _ = _service_com_catalogo_preenchido()
    assert service.classificar_confianca(0.1) == "baixa"
    assert service.classificar_confianca(0.6) == "incerta"
    assert service.classificar_confianca(0.95) == "alta"
