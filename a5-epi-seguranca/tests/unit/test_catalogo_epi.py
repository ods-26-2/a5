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


def test_resolver_epi_por_alias_nome_e_id():
    service = CatalogoEPIService(repo=CatalogoRepository())
    assert service.resolver_epi("helmet") == "capacete"
    assert service.resolver_epi("  CAPACETE ") == "capacete"
    assert service.resolver_epi("Oculos de protecao") == "oculos"
    assert service.resolver_epi("Óculos") == "oculos"
    assert service.resolver_epi("gloves") == "luvas"
    assert service.resolver_epi("nada") is None


def test_sincronizar_zona_adiciona_e_desativa():
    service = CatalogoEPIService(repo=CatalogoRepository())
    service.sincronizar_zona("z", ["capacete", "luvas"])
    service.sincronizar_zona("z", ["capacete", "colete"])
    exigidos = {e.epi_id for e in service.listar_exigidos_na_zona("z")}
    assert exigidos == {"capacete", "colete"}
