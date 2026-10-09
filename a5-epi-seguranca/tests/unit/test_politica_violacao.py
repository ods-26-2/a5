import pytest
from pydantic import ValidationError

from src.a5.integrations.s2_client import S2ClientMock
from src.a5.modules.catalogo_epi.repository import CatalogoRepository
from src.a5.modules.catalogo_epi.service import CatalogoEPIService
from src.a5.modules.politica_violacao.models import NovaPolitica
from src.a5.modules.politica_violacao.repository import PoliticaRepository
from src.a5.modules.politica_violacao.service import PoliticaViolacaoService


def _service():
    catalogo = CatalogoEPIService(repo=CatalogoRepository())
    s2 = S2ClientMock()
    service = PoliticaViolacaoService(
        repo=PoliticaRepository(), s2_client=s2, catalogo_service=catalogo
    )
    return service, s2, catalogo


def _nova(zona_id="zona-1", equipamentos=("capacete",), **extra):
    return NovaPolitica(
        zona={"id": zona_id, "nome": "Zona 1"},
        equipamentos_obrigatorios=list(equipamentos),
        **extra,
    )


def test_definir_politica_envia_documento_para_s2():
    service, s2, _ = _service()
    politica = service.definir_politica(_nova(equipamentos=["capacete", "colete", "luvas"]))
    assert politica.zona.id == "zona-1"
    assert politica.versao == 1
    assert len(s2._enviados) == 1

    doc = s2._enviados[0]
    assert doc.policy_id == "politica-zona-1"
    assert doc.version == 1
    assert doc.person_class == "pessoa"
    assert [r.epi for r in doc.required_equipment] == ["capacete", "colete", "luvas"]
    assert "helmet" in doc.class_aliases["capacete"]
    assert set(doc.class_aliases) == {"capacete", "colete", "luvas"}


def test_equipamento_aceita_alias_e_caixa_diferente():
    service, _, _ = _service()
    politica = service.definir_politica(_nova(equipamentos=["HELMET", "Colete", "LUVA"]))
    assert [e.epi_id for e in politica.equipamentos_obrigatorios] == ["capacete", "colete", "luvas"]


def test_epi_desconhecido_falha():
    service, _, _ = _service()
    with pytest.raises(ValueError, match="nao existe"):
        service.definir_politica(_nova(equipamentos=["epi-fantasma"]))


def test_epi_repetido_via_alias_falha():
    service, _, _ = _service()
    with pytest.raises(ValueError, match="mais de uma vez"):
        service.definir_politica(_nova(equipamentos=["capacete", "helmet"]))


def test_cada_definicao_cria_nova_versao_e_a_ultima_e_a_vigente():
    service, s2, _ = _service()
    service.definir_politica(_nova(equipamentos=["capacete"]))
    v2 = service.definir_politica(_nova(equipamentos=["capacete", "colete"]))
    assert v2.versao == 2
    assert service.politica_vigente("zona-1").versao == 2
    assert [p.versao for p in service.listar_versoes("zona-1")] == [1, 2]
    assert len(service.listar_vigentes()) == 1
    assert s2._enviados[-1].version == 2


def test_id_de_politica_nao_pode_ser_reusado_em_outra_zona():
    service, _, _ = _service()
    service.definir_politica(_nova(zona_id="zona-1", id="obra-civil-sp"))
    with pytest.raises(ValueError, match="ja pertence"):
        service.definir_politica(_nova(zona_id="zona-2", id="obra-civil-sp"))


def test_tolerancia_e_confianca_por_equipamento_herdam_o_padrao():
    service, _, _ = _service()
    nova = NovaPolitica(
        zona={"id": "zona-1"},
        equipamentos_obrigatorios=[
            {"epi_id": "capacete", "tempo_tolerancia_segundos": 3, "confianca_minima": 0.9},
            {"epi_id": "luvas"},
        ],
        tempo_tolerancia_segundos=20,
        confianca_minima=0.5,
    )
    reqs = {r.epi_id: r for r in service.definir_politica(nova).requisitos()}
    assert (reqs["capacete"].tempo_tolerancia_segundos, reqs["capacete"].confianca_minima) == (3, 0.9)
    assert (reqs["luvas"].tempo_tolerancia_segundos, reqs["luvas"].confianca_minima) == (20, 0.5)


def test_catalogo_da_zona_reflete_a_politica_vigente():
    service, _, catalogo = _service()
    service.definir_politica(_nova(equipamentos=["capacete", "luvas"]))
    assert catalogo.epi_exigido_na_zona("zona-1", "luvas")
    service.definir_politica(_nova(equipamentos=["capacete", "colete"]))
    assert catalogo.epi_exigido_na_zona("zona-1", "colete")
    assert not catalogo.epi_exigido_na_zona("zona-1", "luvas")


def test_zona_com_poligono_invalido_e_recusada():
    with pytest.raises(ValidationError):
        NovaPolitica(
            zona={"id": "z", "poligono": [{"x": 0.1, "y": 0.1}, {"x": 0.5, "y": 0.5}]},
            equipamentos_obrigatorios=["capacete"],
        )
    with pytest.raises(ValidationError):
        NovaPolitica(
            zona={"id": "z", "poligono": [{"x": 0, "y": 0}, {"x": 2, "y": 0}, {"x": 1, "y": 1}]},
            equipamentos_obrigatorios=["capacete"],
        )


def test_politica_sem_equipamentos_e_recusada():
    with pytest.raises(ValidationError):
        NovaPolitica(zona={"id": "z"}, equipamentos_obrigatorios=[])


def test_classificar_confianca():
    service, _, _ = _service()
    assert service.classificar_confianca(0.1) == "baixa"
    assert service.classificar_confianca(0.6) == "incerta"
    assert service.classificar_confianca(0.95) == "alta"
