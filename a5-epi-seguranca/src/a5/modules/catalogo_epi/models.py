from pydantic import BaseModel, Field


class EPI(BaseModel):
    id: str
    nome: str
    ativo: bool = True
    # Nomes de classe que o detector (I9) pode emitir para este EPI
    # (ex.: "helmet" -> capacete). A comparacao ignora caixa e acentos.
    aliases: list[str] = Field(default_factory=list)


class CatalogoEntrada(BaseModel):
    id: str
    zona_id: str
    epi_id: str
    ativo: bool = True


class NovaEntradaCatalogo(BaseModel):
    zona_id: str
    epi_id: str


class NovoEPI(BaseModel):
    id: str = Field(..., min_length=1, pattern=r"^[a-z0-9_]+$")
    nome: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)


class AtualizarEPI(BaseModel):
    nome: str | None = Field(None, min_length=1)
    aliases: list[str] | None = None
    ativo: bool | None = None
