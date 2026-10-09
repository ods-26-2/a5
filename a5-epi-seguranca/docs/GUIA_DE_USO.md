# Guia de Uso — Backend do A5 (EPI - Segurança)

Squad VER-3 · ODS 2026/2 · v6

Este guia explica passo a passo o que foi construído no scaffold do A5, por que a
estrutura é assim, e como rodar, testar e evoluir o projeto a partir daqui.

---

## 1. O que foi feito e por quê

O objetivo desta primeira entrega foi deixar a **estrutura do backend pronta e
funcional**, mesmo sem nenhum dos outros componentes (I9, S2, S3, S4) existirem
de verdade ainda. Para isso, três decisões guiaram tudo:

1. **Os 4 módulos do A5 viram 4 pastas de verdade.** A "Modularização do A5" do
   documento de arquitetura (Catálogo de EPI, Política de Violação, Gestão de
   Alertas, Front de Supervisão) não ficou só no papel — cada um é uma pasta em
   `src/a5/modules/` com seu próprio `models.py`, `repository.py` e `service.py`.
   Isso significa que o código reflete exatamente o que está documentado, e
   qualquer pessoa do squad consegue abrir o documento e o código lado a lado.

2. **Tudo que vem de fora é uma interface, não uma chamada direta.** I9, S2, S3
   e S4 são consumidos por contrato (por isso "integrations", não "clients
   diretos"). Cada um tem uma classe abstrata (`I9Client`, `S2Client`, etc.) e,
   hoje, só uma implementação: a mock. Quando o componente real existir, o
   squad correspondente publica o contrato, você escreve uma nova classe que
   implementa a mesma interface, e troca em um lugar só — nenhum módulo do A5
   precisa saber a diferença.

3. **O front nunca fala com I9/S2/S3/S4 diretamente (RF8).** Todos os
   endpoints em `src/a5/api/` só chamam `service`s dos módulos. Os `service`s é
   que decidem quando chamar uma integração mockada.

O resultado: dá para desenvolver, testar e demonstrar o A5 inteiro **hoje**,
sem esperar nenhum outro squad, e trocar os mocks por integrações reais depois
sem reescrever nada além do arquivo do cliente.

---

## 2. Mapa da pasta

```
a5-epi-seguranca/
├── README.md                  ← visão geral rápida (a versão curta deste guia)
├── requirements.txt           ← dependências Python
├── .env.example                ← variáveis de ambiente (copiar para .env)
├── docs/
│   └── contratos.md            ← payloads assumidos para I9/S2/S3/S4 (a validar depois)
├── src/a5/
│   ├── main.py                  ← ponto de entrada (cria o app FastAPI)
│   ├── config.py                ← lê o .env
│   ├── api/                     ← endpoints HTTP, um arquivo por área
│   ├── modules/                 ← os 4 módulos oficiais do A5 (a parte que importa)
│   │   ├── catalogo_epi/
│   │   ├── politica_violacao/
│   │   ├── gestao_alertas/
│   │   └── front_supervisao/
│   ├── integrations/            ← clientes mockados de I9, S2, S3, S4
│   │   └── contracts/            ← envelope B1 assumido
│   ├── mocks/fixtures/          ← dados de exemplo (JSON) que os mocks devolvem
│   ├── auth/                    ← perfis e permissões (RF9)
│   └── db/                      ← onde entra um banco real, quando houver
├── tests/
│   ├── unit/                    ← um teste por módulo
│   └── integration/              ← o fluxo completo, ponta a ponta
└── gerar_estrutura.py            ← o script que gerou tudo isso (útil para recriar do zero)
```

---

## 3. Passo a passo para rodar

### 3.1 Pré-requisitos

- Python 3.10 ou mais novo instalado (`python3 --version` para conferir)

### 3.2 Instalação

```bash
# 1. Extrair o zip e entrar na pasta
unzip a5-epi-seguranca.zip
cd a5-epi-seguranca

# 2. Criar e ativar um ambiente virtual (isola as dependências deste projeto)
python3 -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Copiar o arquivo de configuração de exemplo
cp .env.example .env
```

Você não precisa editar o `.env` para rodar localmente — os valores padrão já
apontam tudo para os clientes mock.

### 3.3 Subindo o servidor

```bash
uvicorn src.a5.main:app --reload
```

Se tudo estiver certo, o terminal mostra algo como:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 3.4 Testando pela interface interativa (Swagger)

Abra **http://localhost:8000/docs** no navegador. O FastAPI gera essa página
sozinho: dá para ver todos os endpoints, expandir cada um, clicar em "Try it
out", preencher os campos e executar direto do navegador — não precisa de
Postman nem de escrever `curl` na mão.

### 3.5 Rodando os testes automatizados

```bash
pytest
```

Deve aparecer `11 passed`. Esses testes já cobrem RF1 a RF8 usando os mocks —
é a forma mais rápida de confirmar que nada quebrou depois de uma alteração.

---

## 4. Um fluxo completo, passo a passo, via Swagger

Esta seção reproduz o mesmo fluxo do caso de uso "Detectar e Tratar Violação
de Uso de EPI", clicando na interface.

1. **Definir a política da zona** (RF1 + RF2)
   `POST /politica/zonas/zona-producao-1`
   ```json
   {
     "zona": {
       "id": "zona-producao-1",
       "nome": "Produção 1",
       "poligono": [{"x": 0.1, "y": 0.1}, {"x": 0.8, "y": 0.1}, {"x": 0.5, "y": 0.9}]
     },
     "classe_pessoa": "pessoa",
     "equipamentos_obrigatorios": [
       "capacete",
       "colete",
       { "epi_id": "luvas", "tempo_tolerancia_segundos": 5, "confianca_minima": 0.8 }
     ],
     "tempo_tolerancia_segundos": 10,
     "confianca_minima": 0.6
   }
   ```
   - **Uma política por zona, com todos os equipamentos dela.** Para mudar os EPIs, envie
     o conjunto completo de novo: cada `POST` cria uma **nova versão** e a última é a vigente
     (`GET /politica/zonas/{zona}`; histórico em `/versoes`; uma por zona em `GET /politica`).
   - Equipamentos aceitam o id, o nome ou qualquer **alias** do catálogo global
     (`GET /catalogo/epis`): `"HELMET"`, `"Capacete"` e `"capacete"` são o mesmo EPI.
     Tolerância e confiança são opcionais por equipamento; sem elas vale o padrão da política.
   - O `poligono` é opcional e usa coordenadas normalizadas [0, 1] (o formato do editor B6).
   - O catálogo da zona (`GET /catalogo/zonas/{zona}`) passa a refletir os equipamentos da
     política. Com política definida, `POST`/`DELETE` no catálogo da zona respondem **409**:
     altere os EPIs salvando uma nova versão da política.
   - Por baixo dos panos, o documento (`policy_id`, `version`, `person_class`, `zone`,
     `required_equipment`, `class_aliases`) vai para o `S2ClientMock` — dá para conferir em
     `src/a5/integrations/s2_client.py` que ele fica guardado em memória.

2. **Consultar o estado atual vindo do I9** (RF3)
   `GET /alertas/zonas/zona-producao-1/estado`
   Retorna os dados de `src/a5/mocks/fixtures/i9_estados.json` — edite esse
   arquivo para simular outros cenários (mais pessoas, outros EPIs, outras
   confianças).

3. **Ver os alertas ativos vindos do S3** (RF4)
   `GET /alertas?zona_id=zona-producao-1`
   Vem de `src/a5/mocks/fixtures/s3_alertas.json`.

4. **Ver a tela de supervisão, já com evidência do S4** (RF7)
   `GET /supervisao/ocorrencias?zona_id=zona-producao-1`
   Junta o alerta do S3 com a evidência do S4 (mock) e monta a descrição —
   é exatamente o que o front vai consumir.

5. **Reconhecer o alerta** (RF5)
   `POST /alertas/{alerta_id}/ack`
   ```json
   { "usuario": "supervisor.joana" }
   ```

6. **Tentar desligar como operador (deve falhar com 403)**
   `POST /alertas/{alerta_id}/desligar`
   ```json
   { "usuario": "operador.carlos", "papel": "operador" }
   ```

7. **Desligar como supervisor (deve funcionar)** (RF6)
   `POST /alertas/{alerta_id}/desligar`
   ```json
   { "usuario": "supervisor.joana", "papel": "supervisor" }
   ```

8. **Conferir no histórico** (RF11)
   `GET /historico?usuario=supervisor.joana`
   Filtros: `zona_id`, `usuario`, `tipo` (`ack`/`mute`/`desligamento`), `desde` e `ate` (ISO-8601).
   O relatório (`GET /historico/relatorio/{zona}`) traz totais por severidade e por EPI e aceita `desde`/`ate`.

---

## 5. Como funcionam os mocks (e como vão deixar de existir)

Cada arquivo em `src/a5/integrations/` segue o mesmo padrão:

```python
class I9Client(ABC):
    @abstractmethod
    def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]: ...

class I9ClientMock(I9Client):
    def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]:
        # lê de um arquivo JSON de exemplo
        ...

def get_i9_client() -> I9Client:
    return I9ClientMock()   # <- é só isso que muda no futuro
```

Quando o I9 estiver publicando eventos de verdade (via B3/Pub-Sub, conforme o
documento de arquitetura), o passo a passo é:

1. Confirmar o schema real do evento com o squad do I9 e atualizar
   `docs/contratos.md`.
2. Criar `I9ClientReal(I9Client)` em `i9_client.py`, implementando
   `obter_estado_atual` para consumir o tópico de verdade.
3. Trocar o `return I9ClientMock()` por uma escolha baseada em
   `settings.i9_client` (o `.env` já tem a variável `A5_I9_CLIENT` reservada
   para isso).

Nenhum `service.py` dos módulos precisa mudar — eles só conhecem a interface
`I9Client`, nunca a implementação concreta.

---

## 6. Rastreabilidade: requisito → código

| Requisito | Onde está |
|---|---|
| RF1 — Catálogo de EPI | `modules/catalogo_epi/` + `api/catalogo.py` (CRUD de EPIs com aliases; catálogo da zona espelha a política) |
| Zonas monitoradas | `modules/zonas/` + `api/zonas.py` (cadastro, polígono, câmera; alterar a geometria gera nova versão da política; `DELETE` desativa e `DELETE ?definitivo=true` apaga, só sem política nem histórico) |
| RF2 — Política de violação | `modules/politica_violacao/` + `api/politica.py` |
| RF3 — Receber estado do I9 | `modules/gestao_alertas/service.py::estado_atual_da_zona` |
| RF4 — Alertas via S3 | `modules/gestao_alertas/service.py::alertas_ativos` |
| RF5 — Reconhecimento (ACK) | `modules/gestao_alertas/service.py::reconhecer` |
| RF6 — Desligamento manual | `modules/gestao_alertas/service.py::desligar_manualmente` + `auth/permissions.py` |
| RF7 — Tela de supervisão | `modules/front_supervisao/` + `api/supervisao.py` |
| RF8 — Isolamento front/back | toda a pasta `api/` só chama `service`s, nunca `integrations/` direto |
| RF9 — Perfis de acesso | `auth/permissions.py` + `auth/service.py` (login, sessão) + `auth/deps.py` (papel por rota) + `api/acessos.py` |
| RF10 — Relatórios | `modules/gestao_alertas/service.py::relatorio_por_zona` + exportação CSV em `api/historico.py` |
| RF11 — Histórico com filtros | `modules/gestao_alertas/service.py::historico` |
| RF12 — Turnos de monitoramento | `modules/politica_violacao/` (`Turno`, `monitoramento_ativo`) + `api/monitoramento.py` (`PUT` troca a grade; `GET .../ativo`) |
| RF13 — Status de conexão | `integrations/health.py` + `GET /health` |
| RNF1 — Auditabilidade | todo ACK/MUTE/desligamento passa por `GestaoAlertasRepository.registrar_acao` |
| RNF2 — Confiança intermediária | `GET /alertas/zonas/{z}/estado` devolve `classificacao` (baixa/incerta/alta); `politica_violacao/service.py::classificar_confianca` + `A5_CONFIANCA_MINIMA`/`MAXIMA` no `.env` |

---

## 7. O que ainda **não** está pronto (de propósito)

Para manter esta primeira entrega enxuta, ficou de fora:

- **Persistência real.** Todos os `repository.py` guardam dados em memória
  (um dicionário Python). Reiniciar o servidor apaga tudo. Quando o time
  decidir o banco (SQL ou não), o lugar certo para plugar é `src/a5/db/`.
- **Autenticação de produção.** Já há login (`POST /auth/login`, token Bearer com
  validade de 8 h, senha com PBKDF2), mas usuários e sessões ficam em memória.
  Para produção, trocar `auth/service.py` por SSO/Supabase Auth mantendo
  `auth/deps.py` como única porta de entrada nas rotas.
- **Clientes reais para I9/S2/S3/S4.** Ver seção 5.
- **CORS e deploy.** O `main.py` está com a configuração mínima do FastAPI,
  sem nada de produção ainda.

---

## 7.0 Login e permissões

- `A5_EXIGIR_LOGIN=false` (padrão): rotas aceitam chamadas **sem** token (usuário/papel no corpo,
  como nos testes antigos). Com token, vale o usuário e o papel **da sessão**, nunca o do corpo.
  `A5_EXIGIR_LOGIN=true`: sem token, 401.
- Em `A5_ENV=development` nascem 4 usuários: `operador`, `supervisor`, `auditor` (senha `<papel>123`)
  e `administrador` (senha `A5_ADMIN_SENHA`, padrão `admin123`). Fora de development só existe o
  administrador, e só se `A5_ADMIN_SENHA` estiver definida.
- Quem pode o quê: configurar zonas/políticas/turnos = supervisor e administrador; EPIs e usuários =
  administrador; histórico e relatórios = supervisor, auditor, administrador; desligar alarme = supervisor
  e administrador; reconhecer/silenciar = qualquer usuário logado.

## 7.1 Rodando em laboratório compartilhado (sem root, sem venv)

Em máquinas de laboratório com `home` montado por rede (NFS) e usuário convidado
(sem `sudo`), o passo `python3 -m venv .venv` pode travar por minutos — cada
arquivo que o venv cria vira uma escrita pela rede — e o Python padrão da
máquina costuma apontar para um ambiente compartilhado e **somente leitura**
(ex.: `/opt/myenv`), o que faz `pip install` falhar com `Permissão negada`.

Se isso acontecer, pule o `venv` inteiramente e instale só para o seu usuário:

```bash
cd a5-epi-seguranca

# instala em ~/.local, sem precisar de venv nem de root
pip install --user -r requirements.txt

# roda via "python -m" para não depender do uvicorn estar no PATH
python3 -m uvicorn src.a5.main:app --reload
```

Rode os comandos **um de cada vez** (não cole o bloco inteiro de uma vez) —
se um comando travar, dar `Ctrl+C` nele pode deixar os comandos seguintes na
fila do terminal e eles rodam fora de ordem, o que gera erros confusos que não
têm relação com o projeto em si.

Se `pip install --user` ainda reclamar de permissão, tente:
```bash
pip install --user --no-cache-dir -r requirements.txt
```

### Se o ambiente for conda (base sempre ativo, `--user` sempre recusado)

Alguns laboratórios têm um ambiente conda "base" que fica sempre ativo e não
pode ser desativado por uma conta convidado — nesse caso `--user` é recusado
por design do conda, mesmo fora de um venv comum. A saída é instalar em uma
pasta própria e depois usar `run.py`/`run_tests.py` (incluídos no projeto),
que inserem essa pasta no `sys.path` de dentro do próprio Python — não depende
de `PYTHONPATH`, que alguns laboratórios travam ou ignoram por segurança:

```bash
mkdir -p ~/a5-libs
pip install --target=~/a5-libs -r requirements.txt

python3 run.py          # sobe o servidor em http://localhost:8000
python3 run_tests.py    # roda os testes
```

Se você instalou os pacotes em outra pasta (não `~/a5-libs`), passe o caminho:
```bash
python3 run.py /caminho/para/sua/pasta
python3 run_tests.py /caminho/para/sua/pasta
```

O `run.py` sobe com `reload=False` de propósito: o modo `--reload` do uvicorn
recria o processo Python por baixo dos panos, e esse novo processo pode não
herdar o ajuste manual de `sys.path` feito pelo `run.py`. Se editar o código,
pare o servidor (`Ctrl+C`) e rode `python3 run.py` de novo.

---

## 8. Comandos rápidos (cola aqui)

```bash
# instalar (máquina própria, com venv)
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# instalar (laboratório compartilhado, sem venv/root — ver seção 7.1)
pip install --user -r requirements.txt

# instalar (laboratório com conda travado — ver seção 7.1)
mkdir -p ~/a5-libs && pip install --target=~/a5-libs -r requirements.txt

# rodar (ambiente normal)
python3 -m uvicorn src.a5.main:app --reload

# rodar (laboratório com conda travado, sem depender de PYTHONPATH)
python3 run.py

# testar
pytest                # ambiente normal
python3 run_tests.py  # laboratório com conda travado

# recriar a estrutura do zero em outra pasta/branch
python3 gerar_estrutura.py outro-nome-de-pasta
```
