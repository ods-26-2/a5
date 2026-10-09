from fastapi.testclient import TestClient

from src.a5.main import app

client = TestClient(app)


def test_politica_via_api_ponta_a_ponta():
    corpo = {
        "zona": {
            "id": "ignorado",
            "nome": "Obra SP - bloco A",
            "poligono": [{"x": 0.1, "y": 0.1}, {"x": 0.8, "y": 0.1}, {"x": 0.5, "y": 0.9}],
        },
        "equipamentos_obrigatorios": ["CAPACETE", "colete", {"epi_id": "glove", "confianca_minima": 0.8}],
        "tempo_tolerancia_segundos": 5,
    }
    r = client.post("/politica/zonas/api-zona-1", json=corpo)
    assert r.status_code == 200, r.text
    dados = r.json()
    assert dados["zona"]["id"] == "api-zona-1"  # o caminho prevalece sobre o corpo
    assert dados["id"] == "politica-api-zona-1"
    assert dados["versao"] == 1
    assert [e["epi_id"] for e in dados["equipamentos_obrigatorios"]] == ["capacete", "colete", "luvas"]

    assert client.post("/politica/zonas/api-zona-1", json=corpo).json()["versao"] == 2
    assert client.get("/politica/zonas/api-zona-1").json()["versao"] == 2
    assert len(client.get("/politica/zonas/api-zona-1/versoes").json()) == 2
    assert any(p["zona"]["id"] == "api-zona-1" for p in client.get("/politica").json())

    # RF1: o catalogo da zona reflete a politica
    catalogo = client.get("/catalogo/zonas/api-zona-1").json()
    assert {e["epi_id"] for e in catalogo} == {"capacete", "colete", "luvas"}


def test_politica_epi_invalido_retorna_400_e_zona_sem_politica_404():
    r = client.post(
        "/politica/zonas/api-zona-2",
        json={"zona": {"id": "x"}, "equipamentos_obrigatorios": ["foguete"]},
    )
    assert r.status_code == 400
    assert client.get("/politica/zonas/zona-que-nao-existe").status_code == 404


def test_uma_politica_por_zona_com_todos_os_equipamentos_mesmo_apos_varias_versoes():
    def salvar(equipamentos):
        r = client.post(
            "/politica/zonas/api-zona-unica",
            json={"zona": {"id": "x"}, "equipamentos_obrigatorios": equipamentos},
        )
        assert r.status_code == 200, r.text
        return r.json()

    salvar(["capacete"])
    salvar(["capacete", "colete"])
    v3 = salvar(["capacete", "colete", "luvas", "oculos"])
    assert v3["versao"] == 3

    # so existe UMA politica vigente para a zona, com o conjunto completo
    vigentes = [p for p in client.get("/politica").json() if p["zona"]["id"] == "api-zona-unica"]
    assert len(vigentes) == 1
    assert [e["epi_id"] for e in vigentes[0]["equipamentos_obrigatorios"]] == [
        "capacete", "colete", "luvas", "oculos",
    ]
    assert vigentes[0]["zona"]["espaco_coordenadas"] == "imagem_normalizada"
    # as versoes anteriores ficam so como historico
    assert [p["versao"] for p in client.get("/politica/zonas/api-zona-unica/versoes").json()] == [1, 2, 3]


def test_catalogo_de_zona_com_politica_nao_e_editado_por_fora():
    client.post(
        "/politica/zonas/api-zona-catalogo",
        json={"zona": {"id": "x"}, "equipamentos_obrigatorios": ["capacete"]},
    )
    r = client.post("/catalogo/zonas/api-zona-catalogo", json={"zona_id": "x", "epi_id": "luvas"})
    assert r.status_code == 409 and "nova versao" in r.json()["detail"]

    entrada = client.get("/catalogo/zonas/api-zona-catalogo").json()[0]
    assert client.delete(f"/catalogo/entradas/{entrada['id']}").status_code == 409

    # zona sem politica continua editavel pelo catalogo
    assert client.post("/catalogo/zonas/api-zona-livre", json={"zona_id": "x", "epi_id": "luvas"}).status_code == 200


def test_historico_e_relatorio_via_api():
    alertas = client.get("/alertas", params={"zona_id": "zona-producao-1"}).json()
    client.post(f"/alertas/{alertas[0]['alerta_id']}/ack", json={"usuario": "auditoria.api"})
    h = client.get("/historico", params={"zona_id": "zona-producao-1", "usuario": "auditoria.api", "tipo": "ack"}).json()
    assert len(h) == 1 and h[0]["zona_id"] == "zona-producao-1"
    r = client.get("/historico/relatorio/zona-producao-1", params={"desde": "2026-09-01T00:00:00"}).json()
    assert r["por_epi"] == {"capacete": 1}
