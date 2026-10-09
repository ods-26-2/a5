from fastapi.testclient import TestClient

from src.a5.main import app

client = TestClient(app)
TRI = [{"x": 0.1, "y": 0.1}, {"x": 0.8, "y": 0.1}, {"x": 0.5, "y": 0.9}]
TRI2 = [{"x": 0.2, "y": 0.2}, {"x": 0.7, "y": 0.2}, {"x": 0.4, "y": 0.8}]


def test_crud_de_zona():
    r = client.post("/zonas", json={"id": "z-crud", "nome": "Crud", "camera_id": "cam-1", "poligono": TRI})
    assert r.status_code == 201, r.text
    assert client.post("/zonas", json={"id": "z-crud"}).status_code == 409
    assert client.post("/zonas", json={"id": "z-ruim", "poligono": TRI[:2]}).status_code == 422

    r = client.put("/zonas/z-crud", json={"nome": "Crud 2"})
    assert r.json()["nome"] == "Crud 2" and len(r.json()["poligono"]) == 3  # poligono preservado

    r = client.put("/zonas/z-crud", json={"poligono": []})  # remove geometria
    assert r.json()["poligono"] == []
    assert client.put("/zonas/nao-existe", json={"nome": "x"}).status_code == 404

    assert client.delete("/zonas/z-crud").json()["ativa"] is False
    # id de zona desativada nao pode ser reaproveitado por uma zona nova
    r = client.post("/zonas", json={"id": "z-crud"})
    assert r.status_code == 409 and "desativada" in r.json()["detail"]
    # reativar
    assert client.put("/zonas/z-crud", json={"ativa": True}).json()["ativa"] is True
    client.delete("/zonas/z-crud")
    assert "z-crud" not in [z["id"] for z in client.get("/zonas").json()]
    assert "z-crud" in [z["id"] for z in client.get("/zonas?incluir_inativas=true").json()]
    # zona desativada nao aceita politica
    r = client.post("/politica/zonas/z-crud", json={"zona": {"id": "z-crud"}, "equipamentos_obrigatorios": ["capacete"]})
    assert r.status_code == 400


def test_politica_usa_zona_cadastrada_e_mudar_geometria_gera_nova_versao():
    client.post("/zonas", json={"id": "z-pol", "nome": "Pol", "poligono": TRI})
    # politica sem geometria herda a da zona cadastrada
    r = client.post("/politica/zonas/z-pol", json={"zona": {"id": "z-pol"}, "equipamentos_obrigatorios": ["capacete", "colete"]})
    assert r.status_code == 200, r.text
    assert len(r.json()["zona"]["poligono"]) == 3 and r.json()["zona"]["nome"] == "Pol"
    assert r.json()["versao"] == 1

    # editar a zona reaplica a politica: versao 2, mesmos equipamentos, nova geometria
    client.put("/zonas/z-pol", json={"poligono": TRI2})
    v = client.get("/politica/zonas/z-pol").json()
    assert v["versao"] == 2
    assert v["zona"]["poligono"][0] == TRI2[0]
    assert [e["epi_id"] for e in v["equipamentos_obrigatorios"]] == ["capacete", "colete"]

    # alterar so a descricao nao gera versao
    client.put("/zonas/z-pol", json={"descricao": "so texto"})
    assert client.get("/politica/zonas/z-pol").json()["versao"] == 2


def test_politica_cria_zona_automaticamente():
    r = client.post("/politica/zonas/z-auto", json={"zona": {"id": "x", "nome": "Auto", "poligono": TRI}, "equipamentos_obrigatorios": ["luvas"]})
    assert r.status_code == 200
    z = client.get("/zonas/z-auto").json()
    assert z["nome"] == "Auto" and len(z["poligono"]) == 3


def test_crud_de_epi_e_aliases():
    r = client.post("/catalogo/epis", json={"id": "protetor_facial", "nome": "Protetor facial", "aliases": ["face shield", "FACE SHIELD", "viseira"]})
    assert r.status_code == 201, r.text
    assert r.json()["aliases"] == ["face shield", "viseira"]  # duplicata (caixa) removida
    assert client.post("/catalogo/epis", json={"id": "protetor_facial", "nome": "x"}).status_code == 400
    # alias que ja e de outro EPI
    assert client.post("/catalogo/epis", json={"id": "outro", "nome": "Outro", "aliases": ["Helmet"]}).status_code == 400

    # novo alias passa a ser aceito na politica
    client.put("/catalogo/epis/protetor_facial", json={"aliases": ["viseira", "visor"]})
    r = client.post("/politica/zonas/z-epi", json={"zona": {"id": "z-epi"}, "equipamentos_obrigatorios": ["VISOR"]})
    assert r.status_code == 200 and r.json()["equipamentos_obrigatorios"][0]["epi_id"] == "protetor_facial"

    # EPI exigido por politica vigente nao pode ser desativado
    assert client.delete("/catalogo/epis/protetor_facial").status_code == 409
    # um livre pode, e depois nao serve mais para politicas novas
    client.post("/catalogo/epis", json={"id": "livre", "nome": "Livre"})
    assert client.delete("/catalogo/epis/livre").json()["ativo"] is False
    r = client.post("/politica/zonas/z-epi2", json={"zona": {"id": "z-epi2"}, "equipamentos_obrigatorios": ["livre"]})
    assert r.status_code == 400
    assert client.put("/catalogo/epis/nao-existe", json={"nome": "x"}).status_code == 404


def test_turnos_substituir_validar_e_monitoramento_ativo():
    assert client.put("/monitoramento/zonas/z-t/turnos", json=[{"inicio": "08:00", "fim": "08:00"}]).status_code == 422
    assert client.put("/monitoramento/zonas/z-t/turnos", json=[{"inicio": "8h", "fim": "12:00"}]).status_code == 422
    r = client.put("/monitoramento/zonas/z-t/turnos", json=[{"inicio": "08:00", "fim": "12:00"}, {"inicio": "22:00", "fim": "06:00"}])
    assert r.status_code == 200 and len(r.json()) == 2
    client.put("/monitoramento/zonas/z-t/turnos", json=[{"inicio": "09:00", "fim": "10:00"}])
    assert client.get("/monitoramento/zonas/z-t/turnos").json() == [{"zona_id": "z-t", "inicio": "09:00", "fim": "10:00"}]

    from datetime import datetime
    from src.a5.modules.politica_violacao.models import Turno
    from src.a5.modules.politica_violacao.service import PoliticaViolacaoService
    svc = PoliticaViolacaoService()
    svc.substituir_turnos("z-noite", [Turno(inicio="22:00", fim="06:00")])
    assert svc.monitoramento_ativo("z-noite", datetime(2026, 1, 1, 23, 30))
    assert svc.monitoramento_ativo("z-noite", datetime(2026, 1, 2, 5, 59))
    assert not svc.monitoramento_ativo("z-noite", datetime(2026, 1, 2, 12, 0))
    assert svc.monitoramento_ativo("zona-sem-turno", datetime(2026, 1, 2, 12, 0))
    client.put("/monitoramento/zonas/z-t/turnos", json=[])
    assert client.get("/monitoramento/zonas/z-t/ativo").json()["ativo"] is True


def test_estado_com_faixa_de_confianca_e_descricao_com_tempo():
    estados = client.get("/alertas/zonas/zona-producao-1/estado").json()
    por_conf = {e["confianca"]: e["classificacao"] for e in estados}
    assert por_conf[0.91] == "alta" and por_conf[0.6] == "incerta"

    oc = client.get("/supervisao/ocorrencias").json()[0]
    assert "ha " in oc["descricao"] and oc["em_violacao_ha_segundos"] > 0


def test_historico_guarda_evidencia_e_exporta_csv():
    client.post("/alertas/alerta-0002/ack", json={"usuario": "csv-user"})
    h = client.get("/historico?usuario=csv-user").json()
    assert h[0]["evidencia_url"].endswith("alerta-0002.mp4")

    r = client.get("/historico/exportar?usuario=csv-user")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    linhas = r.text.lstrip("﻿").strip().splitlines()
    assert linhas[0].startswith("registrado_em,tipo,usuario") and "csv-user" in linhas[1]

    rel = client.get("/historico/relatorio/zona-solda-2/exportar").text.lstrip("﻿")
    assert "dimensao,valor,violacoes" in rel and "epi,oculos,1" in rel


def test_duracao_legivel():
    from src.a5.modules.front_supervisao.service import _duracao
    assert [_duracao(s) for s in (45, 600, 3700, 90000)] == ["45 s", "10 min", "1 h 01 min", "1 d 1 h"]


def test_apagar_zona_definitivamente_so_sem_politica_e_sem_historico():
    # livre: apaga, some ate das inativas, e o id pode ser reaproveitado
    client.post("/zonas", json={"id": "z-apagar"})
    client.put("/monitoramento/zonas/z-apagar/turnos", json=[{"inicio": "08:00", "fim": "09:00"}])
    r = client.delete("/zonas/z-apagar?definitivo=true")
    assert r.status_code == 200 and r.json()["status"] == "apagada"
    assert "z-apagar" not in [z["id"] for z in client.get("/zonas?incluir_inativas=true").json()]
    assert client.get("/monitoramento/zonas/z-apagar/turnos").json() == []
    assert client.post("/zonas", json={"id": "z-apagar"}).status_code == 201
    assert client.delete("/zonas/nao-existe?definitivo=true").status_code == 404

    # com politica: 409, mesmo desativada
    client.post("/politica/zonas/z-apagar", json={"zona": {"id": "z-apagar"}, "equipamentos_obrigatorios": ["capacete"]})
    r = client.delete("/zonas/z-apagar?definitivo=true")
    assert r.status_code == 409 and "politica" in r.json()["detail"]

    # com historico de auditoria: 409
    client.post("/zonas", json={"id": "zona-solda-2"})
    client.post("/alertas/alerta-0002/ack", json={"usuario": "audit-zona"})
    r = client.delete("/zonas/zona-solda-2?definitivo=true")
    assert r.status_code == 409 and "historico" in r.json()["detail"]
