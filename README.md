# A5 · EPI — Segurança

Squad VER-3 · ODS 2026/2 · v6

Detecta e trata violações de uso de EPI. O **backend** (FastAPI) e o **frontend** (Vite + TypeScript) ficam em pastas separadas. I9, S2, S3 e S4 estão **mockados**.

```
a5-epi-seguranca/   backend (API, módulos, mocks, testes)
frontend/           telas (supervisão, zonas, políticas, EPIs, histórico, usuários); usa o kit B6 em vendor/b6/
```

## Rodar

**Backend** (terminal 1):
```bash
cd a5-epi-seguranca
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                                  # 43 testes
uvicorn src.a5.main:app --reload        # http://localhost:8000/docs
```

**Frontend** (terminal 2, com o backend no ar):
```bash
cd frontend
npm install
npm test                                # 30 testes
npm run dev                             # http://localhost:5173
```

Node 18+ e Python 3.10+. **Login (desenvolvimento):** `supervisor` / `supervisor123` (também `operador`, `auditor`; `administrador` / `admin123`). Detalhes do frontend em [`frontend/README.md`](frontend/README.md).

## Como as peças se encaixam

- **Zona** (`/zonas`): id, nome, câmera, polígono e turnos de monitoramento. É cadastrada uma vez.
- **EPI** (`/catalogo/epis`): catálogo global com aliases (nomes que o detector emite, ex.: `HELMET` = `capacete`).
- **Política** (`/politica/zonas/{zona}`): **uma por zona**, com todos os EPIs obrigatórios (tolerância e confiança por EPI, ou o padrão da política). Cada `POST` cria a próxima versão; só a última vale. Mudar o polígono da zona gera nova versão automaticamente.
- **Usuários** (`/usuarios`, `/auth/login`): papéis operador, supervisor, auditor e administrador; o backend usa o papel do token.

```json
POST /politica/zonas/zona-producao-1
{
  "zona": { "id": "zona-producao-1" },
  "equipamentos_obrigatorios": [
    "capacete",
    "colete",
    { "epi_id": "luvas", "tempo_tolerancia_segundos": 5, "confianca_minima": 0.8 }
  ],
  "tempo_tolerancia_segundos": 10,
  "confianca_minima": 0.6
}
```

- O documento enviado ao S2 está em [`docs/contratos.md`](a5-epi-seguranca/docs/contratos.md).
- O catálogo da zona espelha a política; com política definida, editá-lo direto responde 409.
- `A5_EXIGIR_LOGIN=true` no `.env` obriga token em todas as rotas; por padrão, chamadas sem token ainda funcionam.

## Fluxo rápido de teste

1. Entre como `administrador` → **EPIs** (cadastre um novo, se quiser) e **Usuários**.
2. Entre como `supervisor` → **Zonas** → "+ Nova zona" (`zona-producao-1`), desenhe o polígono e adicione turnos.
3. **Políticas** → escolha a zona, marque os EPIs e salve.
4. **Supervisão** → abra uma ocorrência: vídeo com overlay, política da zona, Reconhecer / Silenciar / Desligar.
5. **Histórico** → filtre e exporte em CSV.

## Observações

- Os dados ficam **em memória**: reiniciar o backend apaga zonas, políticas, usuários e histórico (os 4 usuários de desenvolvimento voltam).
- A evidência do S4 mock usa um vídeo de demonstração (precisa de acesso à internet).
- Guia completo do backend, mocks e rastreabilidade RF → código: [`docs/GUIA_DE_USO.md`](a5-epi-seguranca/docs/GUIA_DE_USO.md).
