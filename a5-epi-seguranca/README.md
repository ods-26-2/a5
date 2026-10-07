# A5 · EPI — Segurança

Backend do componente **A5** (Camada 4 · Aplicação), Squad **VER-3**, ODS 2026/2 · v6.

Este repositório implementa **apenas o A5**. Os componentes I9, S2, S3 e S4 são
consumidos por contrato e, enquanto os outros squads não publicam suas APIs reais,
são **mockados** em `src/a5/integrations/`.

## Estrutura

- `src/a5/modules/` — os 4 módulos da modularização oficial do A5:
  `catalogo_epi`, `politica_violacao`, `gestao_alertas`, `front_supervisao`.
  Cada um tem `models.py` (dados), `repository.py` (persistência, hoje em
  memória) e `service.py` (regra de negócio — é o que tem RF/RNF no docstring).
- `src/a5/api/` — os endpoints HTTP (FastAPI) que o front consome. Fala só com
  os `service`s dos módulos, nunca com `integrations/` diretamente (RF8).
- `src/a5/integrations/` — clientes para I9, S2, S3 e S4. **Todos mockados agora.**
  Cada cliente tem uma interface (classe abstrata) e uma implementação mock; quando
  o componente real existir, basta criar uma nova implementação da mesma interface
  e trocar no `config.py` — o resto do código não muda.
- `src/a5/mocks/fixtures/` — dados de exemplo que os mocks devolvem.
- `src/a5/auth/` — perfis e permissões (RF9).
- `tests/` — testes unitários por módulo e um teste de integração do fluxo
  ponta-a-ponta (RF1-RF8) usando os mocks.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 -m uvicorn src.a5.main:app --reload
```

Depois acesse `http://localhost:8000/docs` para a documentação interativa (Swagger).

**Em laboratório compartilhado (sem root, sem venv funcionando)** — pule o
`venv` e instale direto para o seu usuário:

```bash
pip install --user -r requirements.txt
python3 -m uvicorn src.a5.main:app --reload
```

**Em laboratório com conda travado** (o `pip --user` é recusado mesmo fora de
venv) — instale numa pasta própria e use `run.py`, que não depende de
`PYTHONPATH`:

```bash
mkdir -p ~/a5-libs
pip install --target=~/a5-libs -r requirements.txt
python3 run.py
```

Veja a seção 7.1 do `GUIA_DE_USO.md` para o diagnóstico completo desses cenários.

## Rodando os testes

```bash
pytest
```

## O que está mockado e onde trocar depois

| Componente externo | Cliente mock | Contrato real (quando existir) |
|---|---|---|
| I9 (estado por item) | `integrations/i9_client.py` | Evento Pub/Sub via B3, envelope B1 |
| S2 (política de violação) | `integrations/s2_client.py` | Comando textual via B3 |
| S3 (alertas, ACK/MUTE) | `integrations/s3_client.py` | Pub/Sub + comando via B3 |
| S4 (evidência de mídia) | `integrations/s4_client.py` | Request/reply via B3, mídia por referência |

Veja `docs/contratos.md` para o formato de payload assumido em cada mock — é o que
o time vai precisar validar com os squads correspondentes assim que os contratos
de B1 estiverem fechados.

## Rastreabilidade RF → módulo

| RF | Módulo |
|---|---|
| RF1, RF9 (parte) | `catalogo_epi` |
| RF2, RF12 | `politica_violacao` |
| RF3, RF4, RF5, RF6, RF10, RF11 | `gestao_alertas` |
| RF7, RF8 | `front_supervisao` |
| RF9 (perfis) | `auth` |
| RF13 | `integrations/health.py` |
