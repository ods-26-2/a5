# Frontend do A5 (supervisão de EPI)

Vite + TypeScript, sem framework. Fala **só** com o backend A5 (RF8), pelo prefixo
`/api` (proxy do Vite → `http://127.0.0.1:8000`, então não precisa de CORS).

## Rodar

```bash
# terminal 1 — backend (na pasta a5-epi-seguranca)
uvicorn src.a5.main:app --reload

# terminal 2 — frontend (nesta pasta)
npm install
npm run dev          # http://localhost:5173
```

Outro host de backend: `A5_API_TARGET=http://host:8000 npm run dev`.

Outros comandos: `npm test` (vitest, 30 testes, inclui os originais do B6), `npm run typecheck`, `npm run build`.

## Telas

Entra-se com login; o menu mostra só o que o papel pode usar (o backend é quem autoriza).

| Rota | Quem vê | O que faz |
|---|---|---|
| `#/supervisao` | todos | Ocorrências por severidade, evidência no **OverlayPlayer (B6.1)** com caixas, há quanto tempo dura a violação, política da zona, estado I9 com marca de **dúvida** (confiança intermediária), ACK / mute / desligamento com motivo. Atualiza a cada 10 s. |
| `#/zonas` | todos (edita: supervisor, admin) | Cadastro de zonas: nome, descrição, câmera, polígono no **ZoneEditor (B6.2)** (inclui remover polígono) e turnos de monitoramento. Desativar, reativar ou apagar zona (apagar só sem política e sem histórico). |
| `#/politicas` | todos (edita: supervisor, admin) | Uma política por zona: EPIs obrigatórios com tolerância/confiança próprias, histórico de versões ("Usar como base"). |
| `#/epis` | todos (edita: admin) | Catálogo de EPIs: criar, renomear, aliases, ativar/desativar. |
| `#/historico` | supervisor, auditor, admin | Auditoria de ACK/mute/desligamento com filtros, evidência, relatório da zona e exportação CSV. |
| `#/usuarios` | admin | Cadastro de usuários, papel, desativar, redefinir senha. |

A sessão (token) fica no navegador; se expirar, volta para o login.

## B6 sem interferência

- `vendor/b6/` é cópia **intocada** do kit (inclui os testes e os demos HTML dele). Para atualizar, troque as pastas.
- Toda adaptação está em `src/adapters/b6.ts`: ocorrência → timeline do player, saída do editor → polígono da política, e um workaround para o clique direito do ZoneEditor (ver comentário no arquivo).

## Evidência simulada

O S4 mock devolve `https://s4.mock.local/...` (não existe). Enquanto for mock, o front mostra um vídeo de
demonstração (`VITE_DEMO_VIDEO` para trocar) e avisa na tela. Com um S4 real, a URL é usada como vem.

## Para não commitar esta pasta junto com o backend

```bash
echo "frontend/" >> .git/info/exclude   # só na sua cópia local; ninguém mais é afetado
```
