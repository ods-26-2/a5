from src.a5.modules.catalogo_epi.models import NovaEntradaCatalogo
from src.a5.modules.catalogo_epi.repository import CatalogoRepository
from src.a5.modules.catalogo_epi.service import CatalogoEPIService


def test_cadastrar_epi_valido():
    service = CatalogoEPIService(repo=CatalogoRepository())
    entrada = service.cadastrar(NovaEntradaCatalogo(zona_id="zona-1", epi_id="capacete"))
    assert entrada.zona_id == "zona-1"
    assert service.epi_exigido_na_zona("zona-1", "capacete") is True


def test_cadastrar_epi_inexistente_falha():
    service = CatalogoEPIService(repo=CatalogoRepository())
    try:
        service.cadastrar(NovaEntradaCatalogo(zona_id="zona-1", epi_id="epi-fantasma"))
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


def test_desativar_entrada():
    service = CatalogoEPIService(repo=CatalogoRepository())
    entrada = service.cadastrar(NovaEntradaCatalogo(zona_id="zona-1", epi_id="luvas"))
    assert service.desativar(entrada.id) is True
    assert service.epi_exigido_na_zona("zona-1", "luvas") is False
