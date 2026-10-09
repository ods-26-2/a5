import pytest
from fastapi.testclient import TestClient

from src.a5.config import settings
from src.a5.main import app

client = TestClient(app)


def _login(usuario: str, senha: str):
    return client.post("/auth/login", json={"id": usuario, "senha": senha})


def _h(usuario: str, senha: str) -> dict:
    return {"Authorization": f"Bearer {_login(usuario, senha).json()['token']}"}


def test_login_e_sessao():
    assert _login("admin-inexistente", "x").status_code == 401
    assert _login("supervisor", "errada").status_code == 401
    r = _login("supervisor", "supervisor123")
    assert r.status_code == 200 and r.json()["usuario"]["papel"] == "supervisor"
    assert "senha" not in r.text
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert client.get("/auth/eu", headers=h).json()["id"] == "supervisor"
    client.post("/auth/logout", headers=h)
    assert client.get("/auth/eu", headers=h).status_code == 401
    assert client.get("/zonas", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_papel_vem_da_sessao_e_nao_do_corpo():
    op = _h("operador", "operador123")
    # operador tentando se passar por supervisor no corpo: vale o papel da sessao
    r = client.post("/alertas/alerta-0001/desligar", headers=op, json={"usuario": "x", "papel": "supervisor"})
    assert r.status_code == 403
    sup = _h("supervisor", "supervisor123")
    r = client.post("/alertas/alerta-0001/desligar", headers=sup, json={"motivo": "teste"})
    assert r.status_code == 200 and r.json()["usuario"] == "supervisor"


def test_permissoes_por_papel():
    op, sup, aud = (_h(u, f"{u}123") for u in ("operador", "supervisor", "auditor"))
    adm = _h("administrador", "admin123")
    zona = {"id": "z-perm"}
    assert client.post("/zonas", json=zona, headers=op).status_code == 403
    assert client.post("/zonas", json=zona, headers=sup).status_code == 201
    assert client.post("/catalogo/epis", json={"id": "x_epi", "nome": "X"}, headers=sup).status_code == 403
    assert client.post("/catalogo/epis", json={"id": "x_epi", "nome": "X"}, headers=adm).status_code == 201
    assert client.get("/usuarios", headers=sup).status_code == 403
    assert client.get("/historico", headers=op).status_code == 403
    assert client.get("/historico", headers=aud).status_code == 200


def test_administrador_gerencia_usuarios():
    adm = _h("administrador", "admin123")
    r = client.post("/usuarios", headers=adm, json={"id": "ana", "nome": "Ana", "papel": "operador", "senha": "abcd"})
    assert r.status_code == 200 and "senha" not in r.json()
    assert client.post("/usuarios", headers=adm, json={"id": "ana", "nome": "Ana", "papel": "operador"}).status_code == 400
    assert _login("ana", "abcd").status_code == 200
    client.patch("/usuarios/ana", headers=adm, json={"papel": "auditor"})
    assert _login("ana", "abcd").json()["usuario"]["papel"] == "auditor"
    tok = {"Authorization": f"Bearer {_login('ana', 'abcd').json()['token']}"}
    client.patch("/usuarios/ana", headers=adm, json={"ativo": False})
    assert _login("ana", "abcd").status_code == 401
    assert client.get("/auth/eu", headers=tok).status_code == 401  # sessao encerrada ao desativar
    # nao pode remover o ultimo administrador
    assert client.patch("/usuarios/administrador", headers=adm, json={"ativo": False}).status_code == 400


def test_exigir_login_bloqueia_chamadas_anonimas(monkeypatch):
    assert client.get("/zonas").status_code == 200  # modo padrao: anonimo aceito
    monkeypatch.setattr(settings, "exigir_login", True)
    assert client.get("/zonas").status_code == 401
    assert client.post("/alertas/alerta-0001/ack", json={"usuario": "x"}).status_code == 401
    assert client.get("/zonas", headers=_h("operador", "operador123")).status_code == 200
