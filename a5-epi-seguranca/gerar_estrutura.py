"""
Gera a estrutura de pastas e arquivos do componente A5 (EPI - Segurança).
Squad VER-3 · ODS 2026/2 · v6

Uso:
    python3 build_scaffold.py [pasta_destino]

Roda uma vez para criar o projeto do zero. Não sobrescreve arquivos existentes
(gera erro se a pasta destino já existir) para evitar apagar trabalho feito depois.
"""
import os
import sys
import textwrap

ROOT = sys.argv[1] if len(sys.argv) > 1 else "a5-epi-seguranca"

FILES = {}

def add(path, content):
    FILES[path] = textwrap.dedent(content).lstrip("\n")

# ---------------------------------------------------------------------------
# Raiz do projeto
# ---------------------------------------------------------------------------

add("README.md", """
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
    uvicorn src.a5.main:app --reload
    ```

    Depois acesse `http://localhost:8000/docs` para a documentação interativa (Swagger).

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
    """)

add("requirements.txt", """
    fastapi==0.115.0
    uvicorn[standard]==0.30.6
    pydantic==2.9.2
    pydantic-settings==2.5.2
    pytest==8.3.3
    httpx==0.27.2
    """)

add(".env.example", """
    # Ambiente do backend A5
    A5_ENV=development
    A5_LOG_LEVEL=INFO

    # Quando os componentes reais existirem, trocar para "real" liga os clientes de
    # verdade (a implementar); por enquanto só "mock" existe.
    A5_I9_CLIENT=mock
    A5_S2_CLIENT=mock
    A5_S3_CLIENT=mock
    A5_S4_CLIENT=mock

    # Faixa de confiança intermediária (RNF2 / RF-orquestração de incerteza)
    A5_CONFIANCA_MINIMA=0.4
    A5_CONFIANCA_MAXIMA=0.8
    """)

add(".gitignore", """
    __pycache__/
    *.pyc
    .venv/
    .env
    .pytest_cache/
    *.egg-info/
    .DS_Store
    """)

# ---------------------------------------------------------------------------
# src/a5 — raiz do pacote
# ---------------------------------------------------------------------------

add("src/__init__.py", "")

add("src/a5/__init__.py", """
    \"\"\"Componente A5 · EPI - Segurança (Camada 4, Squad VER-3).\"\"\"
    """)

add("src/a5/config.py", """
    \"\"\"Configuração do A5, lida do ambiente (.env).\"\"\"
    from pydantic_settings import BaseSettings, SettingsConfigDict


    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", env_prefix="A5_")

        env: str = "development"
        log_level: str = "INFO"

        i9_client: str = "mock"
        s2_client: str = "mock"
        s3_client: str = "mock"
        s4_client: str = "mock"

        # RNF2 / RF-orquestração: faixa de confiança intermediária vira "incerto",
        # nunca ação automática nem silêncio.
        confianca_minima: float = 0.4
        confianca_maxima: float = 0.8


    settings = Settings()
    """)

add("src/a5/main.py", """
    \"\"\"Ponto de entrada do backend do A5 (FastAPI).\"\"\"
    from fastapi import FastAPI

    from src.a5.api import (
        acessos,
        alertas,
        catalogo,
        historico,
        monitoramento,
        politica,
        supervisao,
    )

    app = FastAPI(
        title="A5 · EPI - Segurança",
        description="Backend do componente A5 (Squad VER-3, ODS 2026/2 v6). "
        "Componentes I9, S2, S3 e S4 estao mockados em src/a5/integrations/.",
        version="0.1.0",
    )

    app.include_router(catalogo.router)
    app.include_router(politica.router)
    app.include_router(alertas.router)
    app.include_router(supervisao.router)
    app.include_router(historico.router)
    app.include_router(acessos.router)
    app.include_router(monitoramento.router)


    @app.get("/health", tags=["saude"])
    def health():
        \"\"\"RF13 - status agregado do A5 e das dependencias externas mockadas.\"\"\"
        from src.a5.integrations.health import check_dependencies

        return check_dependencies()
    """)

# ---------------------------------------------------------------------------
# src/a5/integrations/contracts — envelope B1
# ---------------------------------------------------------------------------

add("src/a5/integrations/__init__.py", "")

add("src/a5/integrations/contracts/__init__.py", "")

add("src/a5/integrations/contracts/envelope.py", """
    \"\"\"
    Envelope comum definido pela frente B1 (origem, horario, confianca, versao).

    Este e um MODELO ASSUMIDO para desenvolvimento local. Quando B1 publicar o
    schema oficial, substituir os campos aqui e re-gerar os mocks que o usam.
    \"\"\"
    from datetime import datetime
    from typing import Optional
    from pydantic import BaseModel, Field


    class EnvelopeB1(BaseModel):
        origem: str = Field(..., description="Componente/squad que publicou o evento, ex: 'I9'")
        tempo_captura: datetime = Field(..., description="Tempo de captura (B2), nao o de recebimento")
        sessao: str = Field(..., description="Sessao de execucao ou replay (B2)")
        sequencia: int = Field(..., description="Numero de sequencia dentro da sessao")
        confianca: Optional[float] = Field(None, ge=0.0, le=1.0)
        versao_artefato: str = Field(..., description="Versao do modelo/artefato que gerou o dado")
        versao_schema: str = Field("1.0.0", description="Versao do schema do payload (B1)")
    """)

# ---------------------------------------------------------------------------
# src/a5/integrations — clientes mockados
# ---------------------------------------------------------------------------

add("src/a5/integrations/i9_client.py", """
    \"\"\"
    Cliente para o I9 (Conformidade de uso relacional - Camada 2).

    Contrato assumido (RF3): I9 expoe o estado por item de EPI para uma pessoa em
    uma zona - correto / incorreto / ausente - com confianca por item. Ver
    docs/contratos.md para o payload completo assumido.

    Quando o I9 real existir (evento Pub/Sub via B3), criar `I9ClientReal` que
    implementa `I9Client` e trocar em config.py / composicao de dependencias.
    Nada no resto do A5 deve mudar.
    \"\"\"
    import json
    from abc import ABC, abstractmethod
    from pathlib import Path
    from typing import Literal

    from pydantic import BaseModel

    EstadoEPI = Literal["correto", "incorreto", "ausente"]

    FIXTURES = Path(__file__).resolve().parent.parent / "mocks" / "fixtures" / "i9_estados.json"


    class EstadoItemEPI(BaseModel):
        pessoa_id: str
        zona_id: str
        epi: str
        estado: EstadoEPI
        confianca: float


    class I9Client(ABC):
        @abstractmethod
        def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]:
            \"\"\"Retorna o estado por item de EPI para todas as pessoas na zona.\"\"\"


    class I9ClientMock(I9Client):
        \"\"\"Le estados de exemplo de um fixture JSON, sem chamar nada de verdade.\"\"\"

        def __init__(self, fixture_path: Path = FIXTURES):
            self._fixture_path = fixture_path

        def obter_estado_atual(self, zona_id: str) -> list[EstadoItemEPI]:
            dados = json.loads(self._fixture_path.read_text(encoding="utf-8"))
            estados = [EstadoItemEPI(**item) for item in dados]
            return [e for e in estados if e.zona_id == zona_id]


    def get_i9_client() -> I9Client:
        # TODO: quando existir I9ClientReal, escolher aqui com base em settings.i9_client
        return I9ClientMock()
    """)

add("src/a5/integrations/s2_client.py", """
    \"\"\"
    Cliente para o S2 (Regras temporais e eventos - Camada 3, squad VER-6).

    Contrato assumido (RF2): A5 envia os parametros da politica de violacao
    (EPI, tempo, confianca minima, zona) para S2; S2 aplica persistencia minima
    e limiar de confianca e, se a violacao for confirmada, repassa para S3 (o A5
    nao fala com S2 para receber - so para configurar).
    \"\"\"
    from abc import ABC, abstractmethod
    from pydantic import BaseModel


    class ParametrosViolacao(BaseModel):
        epi: str
        zona_id: str
        tempo_tolerancia_segundos: int
        confianca_minima: float


    class S2Client(ABC):
        @abstractmethod
        def enviar_politica(self, parametros: ParametrosViolacao) -> bool:
            \"\"\"Envia/atualiza os parametros de violacao no S2. Retorna sucesso.\"\"\"


    class S2ClientMock(S2Client):
        def __init__(self):
            self._enviados: list[ParametrosViolacao] = []

        def enviar_politica(self, parametros: ParametrosViolacao) -> bool:
            # Simula o envio: so guarda em memoria para inspecao em teste/debug.
            self._enviados.append(parametros)
            return True


    def get_s2_client() -> S2Client:
        # TODO: quando existir S2ClientReal (comando textual via B3), escolher aqui
        return S2ClientMock()
    """)

add("src/a5/integrations/s3_client.py", """
    \"\"\"
    Cliente para o S3 (Alertas e notificacoes - Camada 3, tambem entregue pelo VER-3).

    Contrato assumido: S3 envia alertas qualificados (severidade, canal, dados do
    evento) para o A5; o A5 envia de volta comandos de ACK (reconhecimento) e MUTE
    (silenciamento), distintos do desligamento manual completo (RF6), que e uma
    decisao exclusiva do A5 registrada localmente.
    \"\"\"
    import json
    from abc import ABC, abstractmethod
    from datetime import datetime
    from pathlib import Path
    from typing import Literal

    from pydantic import BaseModel

    Severidade = Literal["baixa", "media", "alta", "critica"]

    FIXTURES = Path(__file__).resolve().parent.parent / "mocks" / "fixtures" / "s3_alertas.json"


    class AlertaS3(BaseModel):
        alerta_id: str
        zona_id: str
        pessoa_id: str
        epi: str
        severidade: Severidade
        criado_em: datetime
        reconhecido: bool = False
        silenciado: bool = False


    class S3Client(ABC):
        @abstractmethod
        def listar_alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
            ...

        @abstractmethod
        def enviar_ack(self, alerta_id: str, usuario: str) -> bool:
            \"\"\"RF5 - reconhecimento do alerta.\"\"\"

        @abstractmethod
        def enviar_mute(self, alerta_id: str, usuario: str) -> bool:
            \"\"\"Silenciamento temporario, distinto do desligamento manual (RF6).\"\"\"


    class S3ClientMock(S3Client):
        def __init__(self, fixture_path: Path = FIXTURES):
            self._fixture_path = fixture_path
            self._acks: dict[str, str] = {}
            self._mutes: dict[str, str] = {}

        def _carregar(self) -> list[AlertaS3]:
            dados = json.loads(self._fixture_path.read_text(encoding="utf-8"))
            alertas = [AlertaS3(**item) for item in dados]
            for a in alertas:
                a.reconhecido = a.alerta_id in self._acks
                a.silenciado = a.alerta_id in self._mutes
            return alertas

        def listar_alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
            alertas = self._carregar()
            if zona_id:
                alertas = [a for a in alertas if a.zona_id == zona_id]
            return alertas

        def enviar_ack(self, alerta_id: str, usuario: str) -> bool:
            self._acks[alerta_id] = usuario
            return True

        def enviar_mute(self, alerta_id: str, usuario: str) -> bool:
            self._mutes[alerta_id] = usuario
            return True


    def get_s3_client() -> S3Client:
        # TODO: quando existir S3ClientReal (Pub/Sub + comando via B3), escolher aqui
        return S3ClientMock()
    """)

add("src/a5/integrations/s4_client.py", """
    \"\"\"
    Cliente para o S4 (Evidencia de midia - Camada 3, modulo compartilhado MOD-2).

    Contrato assumido (RF7): A5 pede o descritor de clipe/imagem associado a um
    alerta; midia trafega por referencia (URL/id), nunca embutida no evento.
    \"\"\"
    from abc import ABC, abstractmethod
    from pydantic import BaseModel


    class EvidenciaS4(BaseModel):
        alerta_id: str
        tipo: str  # "imagem" | "clipe"
        url_referencia: str
        inicio_seg: float | None = None
        fim_seg: float | None = None


    class S4Client(ABC):
        @abstractmethod
        def obter_evidencia(self, alerta_id: str) -> EvidenciaS4 | None:
            ...


    class S4ClientMock(S4Client):
        def obter_evidencia(self, alerta_id: str) -> EvidenciaS4 | None:
            # Mock fixo: qualquer alerta devolve uma "evidencia" de exemplo.
            return EvidenciaS4(
                alerta_id=alerta_id,
                tipo="clipe",
                url_referencia=f"https://s4.mock.local/evidencias/{alerta_id}.mp4",
                inicio_seg=0.0,
                fim_seg=6.0,
            )


    def get_s4_client() -> S4Client:
        # TODO: quando existir S4ClientReal (request/reply via B3), escolher aqui
        return S4ClientMock()
    """)

add("src/a5/integrations/health.py", """
    \"\"\"RF13 - status de conexao e sensores: verifica se I9/S2/S3/S4 respondem.\"\"\"
    from src.a5.integrations.i9_client import get_i9_client
    from src.a5.integrations.s2_client import get_s2_client
    from src.a5.integrations.s3_client import get_s3_client
    from src.a5.integrations.s4_client import get_s4_client


    def check_dependencies() -> dict:
        status = {"a5": "ok"}

        try:
            get_i9_client().obter_estado_atual(zona_id="__healthcheck__")
            status["i9"] = "ok"
        except Exception as exc:  # pragma: no cover - so acontece se o mock quebrar
            status["i9"] = f"erro: {exc}"

        try:
            get_s3_client().listar_alertas_ativos()
            status["s3"] = "ok"
        except Exception as exc:  # pragma: no cover
            status["s3"] = f"erro: {exc}"

        status["s2"] = "ok (mock nao verifica handshake)"
        status["s4"] = "ok (mock nao verifica handshake)"
        return status
    """)

# ---------------------------------------------------------------------------
# src/a5/mocks/fixtures — dados de exemplo
# ---------------------------------------------------------------------------

add("src/a5/mocks/__init__.py", "")

add("src/a5/mocks/fixtures/i9_estados.json", """
    [
      {"pessoa_id": "pessoa-001", "zona_id": "zona-producao-1", "epi": "capacete", "estado": "ausente", "confianca": 0.91},
      {"pessoa_id": "pessoa-001", "zona_id": "zona-producao-1", "epi": "luvas", "estado": "correto", "confianca": 0.88},
      {"pessoa_id": "pessoa-002", "zona_id": "zona-producao-1", "epi": "capacete", "estado": "incorreto", "confianca": 0.6},
      {"pessoa_id": "pessoa-003", "zona_id": "zona-solda-2", "epi": "oculos", "estado": "ausente", "confianca": 0.95}
    ]
    """)

add("src/a5/mocks/fixtures/s3_alertas.json", """
    [
      {
        "alerta_id": "alerta-0001",
        "zona_id": "zona-producao-1",
        "pessoa_id": "pessoa-001",
        "epi": "capacete",
        "severidade": "alta",
        "criado_em": "2026-09-23T10:15:00Z"
      },
      {
        "alerta_id": "alerta-0002",
        "zona_id": "zona-solda-2",
        "pessoa_id": "pessoa-003",
        "epi": "oculos",
        "severidade": "critica",
        "criado_em": "2026-09-23T10:20:00Z"
      }
    ]
    """)

add("src/a5/mocks/fixtures/s4_evidencias.json", """
    [
      {"alerta_id": "alerta-0001", "tipo": "clipe", "url_referencia": "https://s4.mock.local/evidencias/alerta-0001.mp4"}
    ]
    """)

# ---------------------------------------------------------------------------
# src/a5/modules/catalogo_epi
# ---------------------------------------------------------------------------

add("src/a5/modules/__init__.py", "")

add("src/a5/modules/catalogo_epi/__init__.py", "")

add("src/a5/modules/catalogo_epi/models.py", """
    from pydantic import BaseModel, Field


    class EPI(BaseModel):
        id: str
        nome: str
        ativo: bool = True


    class CatalogoEntrada(BaseModel):
        id: str
        zona_id: str
        epi_id: str
        ativo: bool = True


    class NovaEntradaCatalogo(BaseModel):
        zona_id: str
        epi_id: str
    """)

add("src/a5/modules/catalogo_epi/repository.py", """
    \"\"\"Persistencia em memoria. Trocar por um repositorio real (SQL) quando houver DB.\"\"\"
    from itertools import count
    from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI

    _EPIS_SEED = [
        EPI(id="capacete", nome="Capacete"),
        EPI(id="luvas", nome="Luvas"),
        EPI(id="oculos", nome="Oculos de protecao"),
        EPI(id="mascara", nome="Mascara"),
        EPI(id="protetor_auricular", nome="Protetor auricular"),
        EPI(id="bota", nome="Bota de seguranca"),
    ]


    class CatalogoRepository:
        def __init__(self):
            self._epis: dict[str, EPI] = {e.id: e for e in _EPIS_SEED}
            self._entradas: dict[str, CatalogoEntrada] = {}
            self._ids = count(1)

        def listar_epis(self) -> list[EPI]:
            return list(self._epis.values())

        def listar_por_zona(self, zona_id: str) -> list[CatalogoEntrada]:
            return [e for e in self._entradas.values() if e.zona_id == zona_id and e.ativo]

        def adicionar(self, zona_id: str, epi_id: str) -> CatalogoEntrada:
            entrada = CatalogoEntrada(id=str(next(self._ids)), zona_id=zona_id, epi_id=epi_id)
            self._entradas[entrada.id] = entrada
            return entrada

        def desativar(self, entrada_id: str) -> bool:
            entrada = self._entradas.get(entrada_id)
            if not entrada:
                return False
            entrada.ativo = False
            return True


    _repo_singleton = CatalogoRepository()


    def get_catalogo_repository() -> CatalogoRepository:
        return _repo_singleton
    """)

add("src/a5/modules/catalogo_epi/service.py", """
    \"\"\"
    Modulo Catalogo de EPI.

    RF1  - Cadastrar catalogo de EPIs exigidos por area/setor.
    RF9  - (parte) impedir configurar politica para EPI fora do catalogo ativo da zona.
    \"\"\"
    from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI, NovaEntradaCatalogo
    from src.a5.modules.catalogo_epi.repository import CatalogoRepository, get_catalogo_repository


    class CatalogoEPIService:
        def __init__(self, repo: CatalogoRepository | None = None):
            self._repo = repo or get_catalogo_repository()

        def listar_epis_disponiveis(self) -> list[EPI]:
            return self._repo.listar_epis()

        def listar_exigidos_na_zona(self, zona_id: str) -> list[CatalogoEntrada]:
            return self._repo.listar_por_zona(zona_id)

        def cadastrar(self, entrada: NovaEntradaCatalogo) -> CatalogoEntrada:
            epis_validos = {e.id for e in self._repo.listar_epis()}
            if entrada.epi_id not in epis_validos:
                raise ValueError(f"EPI '{entrada.epi_id}' nao existe no catalogo global.")
            return self._repo.adicionar(entrada.zona_id, entrada.epi_id)

        def desativar(self, entrada_id: str) -> bool:
            return self._repo.desativar(entrada_id)

        def epi_exigido_na_zona(self, zona_id: str, epi_id: str) -> bool:
            \"\"\"Usado pela Politica de Violacao para validar consistencia (RF9).\"\"\"
            return any(e.epi_id == epi_id for e in self._repo.listar_por_zona(zona_id))
    """)

# ---------------------------------------------------------------------------
# src/a5/modules/politica_violacao
# ---------------------------------------------------------------------------

add("src/a5/modules/politica_violacao/__init__.py", "")

add("src/a5/modules/politica_violacao/models.py", """
    from pydantic import BaseModel, Field


    class PoliticaViolacao(BaseModel):
        id: str
        zona_id: str
        epi_id: str
        tempo_tolerancia_segundos: int = Field(..., ge=0)
        confianca_minima: float = Field(..., ge=0.0, le=1.0)


    class NovaPolitica(BaseModel):
        zona_id: str
        epi_id: str
        tempo_tolerancia_segundos: int = Field(..., ge=0)
        confianca_minima: float = Field(..., ge=0.0, le=1.0)


    class Turno(BaseModel):
        \"\"\"RF12 - horarios de monitoramento ativo por zona.\"\"\"
        zona_id: str
        inicio: str  # "HH:MM"
        fim: str  # "HH:MM"
    """)

add("src/a5/modules/politica_violacao/repository.py", """
    from itertools import count
    from src.a5.modules.politica_violacao.models import PoliticaViolacao, Turno


    class PoliticaRepository:
        def __init__(self):
            self._politicas: dict[str, PoliticaViolacao] = {}
            self._turnos: list[Turno] = []
            self._ids = count(1)

        def salvar(self, politica: PoliticaViolacao) -> PoliticaViolacao:
            self._politicas[politica.id] = politica
            return politica

        def novo_id(self) -> str:
            return str(next(self._ids))

        def listar_por_zona(self, zona_id: str) -> list[PoliticaViolacao]:
            return [p for p in self._politicas.values() if p.zona_id == zona_id]

        def adicionar_turno(self, turno: Turno) -> Turno:
            self._turnos.append(turno)
            return turno

        def listar_turnos(self, zona_id: str) -> list[Turno]:
            return [t for t in self._turnos if t.zona_id == zona_id]


    _repo_singleton = PoliticaRepository()


    def get_politica_repository() -> PoliticaRepository:
        return _repo_singleton
    """)

add("src/a5/modules/politica_violacao/service.py", """
    \"\"\"
    Modulo Politica de Violacao.

    RF2  - Definir politica de violacao (EPI, tempo, confianca, zona); repassa a S2.
    RF12 - Configurar turnos de monitoramento ativo por zona.
    RNF2 - Confianca na faixa intermediaria nunca vira acao automatica nem silencio;
           aqui e onde a faixa e definida (ver config.settings).
    \"\"\"
    from src.a5.config import settings
    from src.a5.integrations.s2_client import ParametrosViolacao, S2Client, get_s2_client
    from src.a5.modules.catalogo_epi.service import CatalogoEPIService
    from src.a5.modules.politica_violacao.models import NovaPolitica, PoliticaViolacao, Turno
    from src.a5.modules.politica_violacao.repository import PoliticaRepository, get_politica_repository


    class PoliticaViolacaoService:
        def __init__(
            self,
            repo: PoliticaRepository | None = None,
            s2_client: S2Client | None = None,
            catalogo_service: CatalogoEPIService | None = None,
        ):
            self._repo = repo or get_politica_repository()
            self._s2 = s2_client or get_s2_client()
            self._catalogo = catalogo_service or CatalogoEPIService()

        def definir_politica(self, nova: NovaPolitica) -> PoliticaViolacao:
            # RF9 (parte): nao permite politica para EPI fora do catalogo ativo da zona.
            if not self._catalogo.epi_exigido_na_zona(nova.zona_id, nova.epi_id):
                raise ValueError(
                    f"EPI '{nova.epi_id}' nao esta no catalogo ativo da zona '{nova.zona_id}'."
                )

            politica = PoliticaViolacao(id=self._repo.novo_id(), **nova.model_dump())
            self._repo.salvar(politica)

            # Repassa os parametros ao S2 (mockado por enquanto).
            self._s2.enviar_politica(
                ParametrosViolacao(
                    epi=politica.epi_id,
                    zona_id=politica.zona_id,
                    tempo_tolerancia_segundos=politica.tempo_tolerancia_segundos,
                    confianca_minima=politica.confianca_minima,
                )
            )
            return politica

        def listar_por_zona(self, zona_id: str) -> list[PoliticaViolacao]:
            return self._repo.listar_por_zona(zona_id)

        def classificar_confianca(self, confianca: float) -> str:
            \"\"\"RNF2 - devolve 'baixa' | 'incerta' | 'alta' conforme a faixa configurada.\"\"\"
            if confianca < settings.confianca_minima:
                return "baixa"
            if confianca > settings.confianca_maxima:
                return "alta"
            return "incerta"

        def definir_turno(self, turno: Turno) -> Turno:
            return self._repo.adicionar_turno(turno)

        def listar_turnos(self, zona_id: str) -> list[Turno]:
            return self._repo.listar_turnos(zona_id)
    """)

# ---------------------------------------------------------------------------
# src/a5/modules/gestao_alertas
# ---------------------------------------------------------------------------

add("src/a5/modules/gestao_alertas/__init__.py", "")

add("src/a5/modules/gestao_alertas/models.py", """
    from datetime import datetime
    from pydantic import BaseModel


    class RegistroDesligamento(BaseModel):
        alerta_id: str
        usuario: str
        registrado_em: datetime
        motivo: str | None = None


    class ReconhecimentoRegistrado(BaseModel):
        alerta_id: str
        usuario: str
        registrado_em: datetime
        tipo: str  # "ack" | "mute" | "desligamento"
    """)

add("src/a5/modules/gestao_alertas/repository.py", """
    from src.a5.modules.gestao_alertas.models import RegistroDesligamento, ReconhecimentoRegistrado


    class GestaoAlertasRepository:
        \"\"\"Historico local de acoes humanas sobre alertas (auditoria - RNF1).\"\"\"

        def __init__(self):
            self._desligamentos: list[RegistroDesligamento] = []
            self._registros: list[ReconhecimentoRegistrado] = []

        def registrar_acao(self, registro: ReconhecimentoRegistrado) -> None:
            self._registros.append(registro)

        def registrar_desligamento(self, registro: RegistroDesligamento) -> None:
            self._desligamentos.append(registro)

        def historico(
            self,
            zona_id: str | None = None,
            usuario: str | None = None,
        ) -> list[ReconhecimentoRegistrado]:
            registros = self._registros
            if usuario:
                registros = [r for r in registros if r.usuario == usuario]
            return registros


    _repo_singleton = GestaoAlertasRepository()


    def get_gestao_alertas_repository() -> GestaoAlertasRepository:
        return _repo_singleton
    """)

add("src/a5/modules/gestao_alertas/service.py", """
    \"\"\"
    Modulo Gestao de Alertas.

    RF3  - Receber estado por item de I9 (via orquestracao simples abaixo).
    RF4  - Disparar/consultar alertas de violacao roteados por S3.
    RF5  - Reconhecimento (ACK) do alerta, com autor e horario.
    RF6  - Desligamento manual do alarme por profissional competente, auditado.
    RF10 - Relatorios analiticos de violacoes.
    RF11 - Consulta de historico com filtros.
    RNF1 - Toda ACK/MUTE/desligamento registra autor e horario.
    \"\"\"
    from datetime import datetime, timezone

    from src.a5.auth.permissions import Papel, usuario_pode_desligar_alarme
    from src.a5.integrations.i9_client import EstadoItemEPI, I9Client, get_i9_client
    from src.a5.integrations.s3_client import AlertaS3, S3Client, get_s3_client
    from src.a5.modules.gestao_alertas.models import RegistroDesligamento, ReconhecimentoRegistrado
    from src.a5.modules.gestao_alertas.repository import (
        GestaoAlertasRepository,
        get_gestao_alertas_repository,
    )


    class GestaoAlertasService:
        def __init__(
            self,
            repo: GestaoAlertasRepository | None = None,
            i9_client: I9Client | None = None,
            s3_client: S3Client | None = None,
        ):
            self._repo = repo or get_gestao_alertas_repository()
            self._i9 = i9_client or get_i9_client()
            self._s3 = s3_client or get_s3_client()

        def estado_atual_da_zona(self, zona_id: str) -> list[EstadoItemEPI]:
            \"\"\"RF3 - estado por item vindo de I9.\"\"\"
            return self._i9.obter_estado_atual(zona_id)

        def alertas_ativos(self, zona_id: str | None = None) -> list[AlertaS3]:
            \"\"\"RF4 - alertas qualificados vindos de S3.\"\"\"
            return self._s3.listar_alertas_ativos(zona_id)

        def reconhecer(self, alerta_id: str, usuario: str) -> bool:
            \"\"\"RF5 - ACK.\"\"\"
            ok = self._s3.enviar_ack(alerta_id, usuario)
            if ok:
                self._repo.registrar_acao(
                    ReconhecimentoRegistrado(
                        alerta_id=alerta_id,
                        usuario=usuario,
                        registrado_em=datetime.now(timezone.utc),
                        tipo="ack",
                    )
                )
            return ok

        def silenciar(self, alerta_id: str, usuario: str) -> bool:
            \"\"\"MUTE - silenciamento temporario, distinto do desligamento (RF6).\"\"\"
            ok = self._s3.enviar_mute(alerta_id, usuario)
            if ok:
                self._repo.registrar_acao(
                    ReconhecimentoRegistrado(
                        alerta_id=alerta_id,
                        usuario=usuario,
                        registrado_em=datetime.now(timezone.utc),
                        tipo="mute",
                    )
                )
            return ok

        def desligar_manualmente(self, alerta_id: str, usuario: str, papel: Papel, motivo: str | None = None):
            \"\"\"RF6 - restrito a profissional competente (RF9/permissoes).\"\"\"
            if not usuario_pode_desligar_alarme(papel):
                raise PermissionError(f"Papel '{papel}' nao pode desligar o alarme manualmente.")

            registro = RegistroDesligamento(
                alerta_id=alerta_id,
                usuario=usuario,
                registrado_em=datetime.now(timezone.utc),
                motivo=motivo,
            )
            self._repo.registrar_desligamento(registro)
            self._repo.registrar_acao(
                ReconhecimentoRegistrado(
                    alerta_id=alerta_id,
                    usuario=usuario,
                    registrado_em=registro.registrado_em,
                    tipo="desligamento",
                )
            )
            return registro

        def historico(self, zona_id: str | None = None, usuario: str | None = None):
            \"\"\"RF11 - consulta de historico com filtros.\"\"\"
            return self._repo.historico(zona_id=zona_id, usuario=usuario)

        def relatorio_por_zona(self, zona_id: str) -> dict:
            \"\"\"RF10 - relatorio analitico simples (contagem por severidade).\"\"\"
            alertas = self.alertas_ativos(zona_id)
            contagem: dict[str, int] = {}
            for a in alertas:
                contagem[a.severidade] = contagem.get(a.severidade, 0) + 1
            return {"zona_id": zona_id, "total": len(alertas), "por_severidade": contagem}
    """)

# ---------------------------------------------------------------------------
# src/a5/modules/front_supervisao
# ---------------------------------------------------------------------------

add("src/a5/modules/front_supervisao/__init__.py", "")

add("src/a5/modules/front_supervisao/dto.py", """
    from pydantic import BaseModel


    class OcorrenciaSupervisao(BaseModel):
        \"\"\"O que o painel de supervisao (RF7) exibe: alerta + evidencia + descricao.\"\"\"
        alerta_id: str
        zona_id: str
        pessoa_id: str
        epi: str
        severidade: str
        descricao: str
        evidencia_url: str | None
    """)

add("src/a5/modules/front_supervisao/service.py", """
    \"\"\"
    Modulo Front de Supervisao.

    RF7 - Exibir violacoes com evidencia (S4) e descricao especifica.
    RF8 - Isolamento: este service e o UNICO ponto que o endpoint de supervisao chama;
          nunca expor I9/S2/S3/S4 diretamente para o front.
    \"\"\"
    from src.a5.integrations.s4_client import S4Client, get_s4_client
    from src.a5.modules.front_supervisao.dto import OcorrenciaSupervisao
    from src.a5.modules.gestao_alertas.service import GestaoAlertasService


    class FrontSupervisaoService:
        def __init__(
            self,
            gestao_alertas: GestaoAlertasService | None = None,
            s4_client: S4Client | None = None,
        ):
            self._gestao_alertas = gestao_alertas or GestaoAlertasService()
            self._s4 = s4_client or get_s4_client()

        def listar_ocorrencias(self, zona_id: str | None = None) -> list[OcorrenciaSupervisao]:
            alertas = self._gestao_alertas.alertas_ativos(zona_id)
            ocorrencias = []
            for a in alertas:
                evidencia = self._s4.obter_evidencia(a.alerta_id)
                ocorrencias.append(
                    OcorrenciaSupervisao(
                        alerta_id=a.alerta_id,
                        zona_id=a.zona_id,
                        pessoa_id=a.pessoa_id,
                        epi=a.epi,
                        severidade=a.severidade,
                        descricao=(
                            f"EPI '{a.epi}' em desconformidade para a pessoa "
                            f"'{a.pessoa_id}' na zona '{a.zona_id}'."
                        ),
                        evidencia_url=evidencia.url_referencia if evidencia else None,
                    )
                )
            return ocorrencias
    """)

# ---------------------------------------------------------------------------
# src/a5/auth
# ---------------------------------------------------------------------------

add("src/a5/auth/__init__.py", "")

add("src/a5/auth/models.py", """
    from pydantic import BaseModel

    from src.a5.auth.permissions import Papel


    class Usuario(BaseModel):
        id: str
        nome: str
        papel: Papel
    """)

add("src/a5/auth/permissions.py", """
    \"\"\"
    RF9 - Perfis de acesso (Operador, Supervisor, Auditor) com permissoes granulares.

    Comeca simples (enum + funcoes puras) de proposito: e facil de testar e de trocar
    por um esquema mais robusto (RBAC com banco) depois, sem afetar quem ja usa
    `usuario_pode_desligar_alarme` etc.
    \"\"\"
    from enum import Enum


    class Papel(str, Enum):
        OPERADOR = "operador"
        SUPERVISOR = "supervisor"
        AUDITOR = "auditor"
        ADMINISTRADOR = "administrador"


    # RF6 - desligamento manual restrito a "profissional competente".
    PAPEIS_QUE_PODEM_DESLIGAR_ALARME = {Papel.SUPERVISOR, Papel.ADMINISTRADOR}


    def usuario_pode_desligar_alarme(papel: Papel) -> bool:
        return papel in PAPEIS_QUE_PODEM_DESLIGAR_ALARME


    def usuario_pode_ver_relatorios(papel: Papel) -> bool:
        return papel in {Papel.SUPERVISOR, Papel.AUDITOR, Papel.ADMINISTRADOR}


    def usuario_pode_configurar_politica(papel: Papel) -> bool:
        return papel in {Papel.SUPERVISOR, Papel.ADMINISTRADOR}
    """)

# ---------------------------------------------------------------------------
# src/a5/db
# ---------------------------------------------------------------------------

add("src/a5/db/__init__.py", "")

add("src/a5/db/session.py", """
    \"\"\"
    Ainda nao ha banco real: os repositories dos modulos guardam tudo em memoria
    (dicionarios/listas em singletons no proprio modulo). Este arquivo existe como
    o lugar unico para plugar SQLAlchemy/Postgres depois, sem espalhar a mudanca.
    \"\"\"


    def get_session():
        raise NotImplementedError(
            "Sem banco real ainda. Os repositories em src/a5/modules/*/repository.py "
            "usam armazenamento em memoria por enquanto (ver P3 / build da aplicacao)."
        )
    """)

# ---------------------------------------------------------------------------
# src/a5/api — endpoints HTTP
# ---------------------------------------------------------------------------

add("src/a5/api/__init__.py", "")

add("src/a5/api/catalogo.py", """
    \"\"\"RF1 - Cadastro do catalogo de EPIs exigidos por zona.\"\"\"
    from fastapi import APIRouter, HTTPException

    from src.a5.modules.catalogo_epi.models import CatalogoEntrada, EPI, NovaEntradaCatalogo
    from src.a5.modules.catalogo_epi.service import CatalogoEPIService

    router = APIRouter(prefix="/catalogo", tags=["catalogo-epi"])
    service = CatalogoEPIService()


    @router.get("/epis", response_model=list[EPI])
    def listar_epis_disponiveis():
        return service.listar_epis_disponiveis()


    @router.get("/zonas/{zona_id}", response_model=list[CatalogoEntrada])
    def listar_exigidos_na_zona(zona_id: str):
        return service.listar_exigidos_na_zona(zona_id)


    @router.post("/zonas/{zona_id}", response_model=CatalogoEntrada)
    def cadastrar_entrada(zona_id: str, entrada: NovaEntradaCatalogo):
        entrada.zona_id = zona_id
        try:
            return service.cadastrar(entrada)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


    @router.delete("/entradas/{entrada_id}")
    def desativar_entrada(entrada_id: str):
        if not service.desativar(entrada_id):
            raise HTTPException(status_code=404, detail="Entrada nao encontrada.")
        return {"status": "desativada"}
    """)

add("src/a5/api/politica.py", """
    \"\"\"RF2 - Politica de violacao por zona/EPI.\"\"\"
    from fastapi import APIRouter, HTTPException

    from src.a5.modules.politica_violacao.models import NovaPolitica, PoliticaViolacao
    from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

    router = APIRouter(prefix="/politica", tags=["politica-violacao"])
    service = PoliticaViolacaoService()


    @router.post("/zonas/{zona_id}", response_model=PoliticaViolacao)
    def definir_politica(zona_id: str, nova: NovaPolitica):
        nova.zona_id = zona_id
        try:
            return service.definir_politica(nova)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


    @router.get("/zonas/{zona_id}", response_model=list[PoliticaViolacao])
    def listar_politicas(zona_id: str):
        return service.listar_por_zona(zona_id)
    """)

add("src/a5/api/alertas.py", """
    \"\"\"RF3, RF4, RF5, RF6 - estado, alertas ativos, ACK, MUTE e desligamento manual.\"\"\"
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    from src.a5.auth.permissions import Papel
    from src.a5.integrations.i9_client import EstadoItemEPI
    from src.a5.integrations.s3_client import AlertaS3
    from src.a5.modules.gestao_alertas.models import RegistroDesligamento
    from src.a5.modules.gestao_alertas.service import GestaoAlertasService

    router = APIRouter(prefix="/alertas", tags=["gestao-alertas"])
    service = GestaoAlertasService()


    class AcaoAlerta(BaseModel):
        usuario: str


    class DesligamentoRequest(BaseModel):
        usuario: str
        papel: Papel
        motivo: str | None = None


    @router.get("/zonas/{zona_id}/estado", response_model=list[EstadoItemEPI])
    def estado_atual(zona_id: str):
        return service.estado_atual_da_zona(zona_id)


    @router.get("", response_model=list[AlertaS3])
    def alertas_ativos(zona_id: str | None = None):
        return service.alertas_ativos(zona_id)


    @router.post("/{alerta_id}/ack")
    def reconhecer(alerta_id: str, acao: AcaoAlerta):
        if not service.reconhecer(alerta_id, acao.usuario):
            raise HTTPException(status_code=400, detail="Falha ao registrar ACK.")
        return {"status": "reconhecido"}


    @router.post("/{alerta_id}/mute")
    def silenciar(alerta_id: str, acao: AcaoAlerta):
        if not service.silenciar(alerta_id, acao.usuario):
            raise HTTPException(status_code=400, detail="Falha ao silenciar.")
        return {"status": "silenciado"}


    @router.post("/{alerta_id}/desligar", response_model=RegistroDesligamento)
    def desligar(alerta_id: str, req: DesligamentoRequest):
        try:
            return service.desligar_manualmente(alerta_id, req.usuario, req.papel, req.motivo)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
    """)

add("src/a5/api/supervisao.py", """
    \"\"\"RF7, RF8 - painel de supervisao (unico ponto que o front consome).\"\"\"
    from fastapi import APIRouter

    from src.a5.modules.front_supervisao.dto import OcorrenciaSupervisao
    from src.a5.modules.front_supervisao.service import FrontSupervisaoService

    router = APIRouter(prefix="/supervisao", tags=["front-supervisao"])
    service = FrontSupervisaoService()


    @router.get("/ocorrencias", response_model=list[OcorrenciaSupervisao])
    def listar_ocorrencias(zona_id: str | None = None):
        return service.listar_ocorrencias(zona_id)
    """)

add("src/a5/api/historico.py", """
    \"\"\"RF10, RF11 - relatorios analiticos e historico com filtros.\"\"\"
    from fastapi import APIRouter

    from src.a5.modules.gestao_alertas.models import ReconhecimentoRegistrado
    from src.a5.modules.gestao_alertas.service import GestaoAlertasService

    router = APIRouter(prefix="/historico", tags=["historico-relatorios"])
    service = GestaoAlertasService()


    @router.get("", response_model=list[ReconhecimentoRegistrado])
    def historico(zona_id: str | None = None, usuario: str | None = None):
        return service.historico(zona_id=zona_id, usuario=usuario)


    @router.get("/relatorio/{zona_id}")
    def relatorio_por_zona(zona_id: str):
        return service.relatorio_por_zona(zona_id)
    """)

add("src/a5/api/acessos.py", """
    \"\"\"RF9 - perfis de acesso (cadastro simples em memoria, para o time evoluir).\"\"\"
    from fastapi import APIRouter, HTTPException

    from src.a5.auth.models import Usuario
    from src.a5.auth.permissions import Papel

    router = APIRouter(prefix="/usuarios", tags=["acessos"])

    _usuarios: dict[str, Usuario] = {}


    @router.post("", response_model=Usuario)
    def cadastrar_usuario(usuario: Usuario):
        _usuarios[usuario.id] = usuario
        return usuario


    @router.get("", response_model=list[Usuario])
    def listar_usuarios():
        return list(_usuarios.values())


    @router.get("/{usuario_id}", response_model=Usuario)
    def obter_usuario(usuario_id: str):
        usuario = _usuarios.get(usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
        return usuario
    """)

add("src/a5/api/monitoramento.py", """
    \"\"\"RF12 - turnos/horarios de monitoramento ativo por zona.\"\"\"
    from fastapi import APIRouter

    from src.a5.modules.politica_violacao.models import Turno
    from src.a5.modules.politica_violacao.service import PoliticaViolacaoService

    router = APIRouter(prefix="/monitoramento", tags=["monitoramento"])
    service = PoliticaViolacaoService()


    @router.post("/zonas/{zona_id}/turnos", response_model=Turno)
    def definir_turno(zona_id: str, turno: Turno):
        turno.zona_id = zona_id
        return service.definir_turno(turno)


    @router.get("/zonas/{zona_id}/turnos", response_model=list[Turno])
    def listar_turnos(zona_id: str):
        return service.listar_turnos(zona_id)
    """)

# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

add("tests/__init__.py", "")
add("tests/unit/__init__.py", "")
add("tests/integration/__init__.py", "")

add("tests/unit/test_catalogo_epi.py", """
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
    """)

add("tests/unit/test_politica_violacao.py", """
    from src.a5.integrations.s2_client import S2ClientMock
    from src.a5.modules.catalogo_epi.models import NovaEntradaCatalogo
    from src.a5.modules.catalogo_epi.repository import CatalogoRepository
    from src.a5.modules.catalogo_epi.service import CatalogoEPIService
    from src.a5.modules.politica_violacao.models import NovaPolitica
    from src.a5.modules.politica_violacao.repository import PoliticaRepository
    from src.a5.modules.politica_violacao.service import PoliticaViolacaoService


    def _service_com_catalogo_preenchido():
        catalogo_repo = CatalogoRepository()
        catalogo_service = CatalogoEPIService(repo=catalogo_repo)
        catalogo_service.cadastrar(NovaEntradaCatalogo(zona_id="zona-1", epi_id="capacete"))
        s2 = S2ClientMock()
        service = PoliticaViolacaoService(
            repo=PoliticaRepository(), s2_client=s2, catalogo_service=catalogo_service
        )
        return service, s2


    def test_definir_politica_envia_para_s2():
        service, s2 = _service_com_catalogo_preenchido()
        politica = service.definir_politica(
            NovaPolitica(zona_id="zona-1", epi_id="capacete", tempo_tolerancia_segundos=10, confianca_minima=0.7)
        )
        assert politica.zona_id == "zona-1"
        assert len(s2._enviados) == 1


    def test_definir_politica_para_epi_fora_do_catalogo_falha():
        service, _ = _service_com_catalogo_preenchido()
        try:
            service.definir_politica(
                NovaPolitica(zona_id="zona-1", epi_id="oculos", tempo_tolerancia_segundos=5, confianca_minima=0.5)
            )
            assert False, "deveria ter levantado ValueError"
        except ValueError:
            pass


    def test_classificar_confianca():
        service, _ = _service_com_catalogo_preenchido()
        assert service.classificar_confianca(0.1) == "baixa"
        assert service.classificar_confianca(0.6) == "incerta"
        assert service.classificar_confianca(0.95) == "alta"
    """)

add("tests/unit/test_gestao_alertas.py", """
    from src.a5.auth.permissions import Papel
    from src.a5.integrations.i9_client import I9ClientMock
    from src.a5.integrations.s3_client import S3ClientMock
    from src.a5.modules.gestao_alertas.repository import GestaoAlertasRepository
    from src.a5.modules.gestao_alertas.service import GestaoAlertasService


    def _service():
        return GestaoAlertasService(
            repo=GestaoAlertasRepository(), i9_client=I9ClientMock(), s3_client=S3ClientMock()
        )


    def test_estado_atual_da_zona_usa_mock_i9():
        service = _service()
        estados = service.estado_atual_da_zona("zona-producao-1")
        assert len(estados) > 0
        assert all(e.zona_id == "zona-producao-1" for e in estados)


    def test_reconhecer_alerta_registra_no_historico():
        service = _service()
        alertas = service.alertas_ativos()
        alerta_id = alertas[0].alerta_id
        assert service.reconhecer(alerta_id, "supervisor.joana") is True
        historico = service.historico(usuario="supervisor.joana")
        assert len(historico) == 1
        assert historico[0].tipo == "ack"


    def test_desligamento_negado_para_operador():
        service = _service()
        alertas = service.alertas_ativos()
        try:
            service.desligar_manualmente(alertas[0].alerta_id, "operador.carlos", Papel.OPERADOR)
            assert False, "operador nao deveria poder desligar"
        except PermissionError:
            pass


    def test_desligamento_permitido_para_supervisor():
        service = _service()
        alertas = service.alertas_ativos()
        registro = service.desligar_manualmente(
            alertas[0].alerta_id, "supervisor.joana", Papel.SUPERVISOR, motivo="situacao resolvida"
        )
        assert registro.usuario == "supervisor.joana"
    """)

add("tests/integration/test_fluxo_violacao.py", """
    \"\"\"
    Fluxo ponta-a-ponta usando os mocks: cadastra EPI, define politica, consulta
    estado (I9 mock), consulta alertas (S3 mock), reconhece e desliga.
    Cobre RF1-RF8 no nivel de integracao entre os 4 modulos do A5.
    \"\"\"
    from src.a5.auth.permissions import Papel
    from src.a5.modules.catalogo_epi.models import NovaEntradaCatalogo
    from src.a5.modules.catalogo_epi.repository import CatalogoRepository
    from src.a5.modules.catalogo_epi.service import CatalogoEPIService
    from src.a5.modules.front_supervisao.service import FrontSupervisaoService
    from src.a5.modules.gestao_alertas.service import GestaoAlertasService
    from src.a5.modules.politica_violacao.models import NovaPolitica
    from src.a5.modules.politica_violacao.repository import PoliticaRepository
    from src.a5.modules.politica_violacao.service import PoliticaViolacaoService


    def test_fluxo_completo_com_mocks():
        catalogo_repo = CatalogoRepository()
        catalogo = CatalogoEPIService(repo=catalogo_repo)
        catalogo.cadastrar(NovaEntradaCatalogo(zona_id="zona-producao-1", epi_id="capacete"))

        politica = PoliticaViolacaoService(repo=PoliticaRepository(), catalogo_service=catalogo)
        politica.definir_politica(
            NovaPolitica(
                zona_id="zona-producao-1",
                epi_id="capacete",
                tempo_tolerancia_segundos=15,
                confianca_minima=0.5,
            )
        )

        gestao = GestaoAlertasService()
        estados = gestao.estado_atual_da_zona("zona-producao-1")
        assert any(e.epi == "capacete" and e.estado == "ausente" for e in estados)

        alertas = gestao.alertas_ativos("zona-producao-1")
        assert len(alertas) >= 1

        supervisao = FrontSupervisaoService(gestao_alertas=gestao)
        ocorrencias = supervisao.listar_ocorrencias("zona-producao-1")
        assert len(ocorrencias) == len(alertas)
        assert all(o.evidencia_url for o in ocorrencias)

        alerta_id = alertas[0].alerta_id
        assert gestao.reconhecer(alerta_id, "supervisor.joana") is True
        registro = gestao.desligar_manualmente(alerta_id, "supervisor.joana", Papel.SUPERVISOR)
        assert registro.alerta_id == alerta_id
    """)

# ---------------------------------------------------------------------------
# docs
# ---------------------------------------------------------------------------

add("docs/contratos.md", """
    # Contratos assumidos para os mocks (a validar com os outros squads)

    Estes payloads sao a MELHOR HIPOTESE do squad VER-3 para o que I9, S2, S3 e S4 vao
    publicar, baseada no que esta descrito no documento de arquitetura. Quando B1
    publicar os schemas oficiais, atualizar aqui e nos `integrations/*.py`.

    ## I9 -> A5 (estado por item)

    ```json
    {
      "pessoa_id": "string",
      "zona_id": "string",
      "epi": "string",
      "estado": "correto | incorreto | ausente",
      "confianca": 0.0
    }
    ```

    ## A5 -> S2 (parametros da politica de violacao)

    ```json
    {
      "epi": "string",
      "zona_id": "string",
      "tempo_tolerancia_segundos": 0,
      "confianca_minima": 0.0
    }
    ```

    ## S3 -> A5 (alerta qualificado)

    ```json
    {
      "alerta_id": "string",
      "zona_id": "string",
      "pessoa_id": "string",
      "epi": "string",
      "severidade": "baixa | media | alta | critica",
      "criado_em": "ISO-8601"
    }
    ```

    ## A5 -> S3 (comandos)

    - `POST /alertas/{id}/ack` — reconhecimento (RF5)
    - `POST /alertas/{id}/mute` — silenciamento temporario
    - Desligamento manual completo (RF6) e decisao e registro **exclusivos do A5**,
      nao um comando enviado a S3 (mas pode evoluir para notificar S3 tambem).

    ## S4 -> A5 (evidencia)

    ```json
    {
      "alerta_id": "string",
      "tipo": "imagem | clipe",
      "url_referencia": "string",
      "inicio_seg": 0.0,
      "fim_seg": 0.0
    }
    ```

    ## Envelope B1 (assumido)

    Ver `src/a5/integrations/contracts/envelope.py`. Campos: origem, tempo_captura,
    sessao, sequencia, confianca, versao_artefato, versao_schema.
    """)


# ---------------------------------------------------------------------------
# Escrita em disco
# ---------------------------------------------------------------------------

def main():
    if os.path.exists(ROOT):
        print(f"ERRO: a pasta '{ROOT}' ja existe. Apague-a ou passe outro nome.")
        raise SystemExit(1)

    for rel_path, content in FILES.items():
        full_path = os.path.join(ROOT, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as fh:
            fh.write(content if content.endswith("\n") or content == "" else content + "\n")

    print(f"Projeto criado em '{ROOT}/' com {len(FILES)} arquivos.")


if __name__ == "__main__":
    main()
