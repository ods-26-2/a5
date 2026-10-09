from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.a5.modules.politica_violacao.models import Ponto


def _validar_poligono(pontos: list[Ponto] | None):
    if pontos and len(pontos) < 3:
        raise ValueError("O poligono da zona precisa de pelo menos 3 pontos.")
    return pontos


class ZonaCadastro(BaseModel):
    """Zona monitorada: onde a politica vale. Cadastro independente da politica."""
    id: str
    nome: str | None = None
    descricao: str | None = None
    camera_id: str | None = None  # vinculo com a camera (S1) quando o contrato existir
    espaco_coordenadas: str = "imagem_normalizada"
    poligono: list[Ponto] = Field(default_factory=list)
    ativa: bool = True
    atualizada_em: datetime


class NovaZona(BaseModel):
    id: str = Field(..., min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")
    nome: str | None = None
    descricao: str | None = None
    camera_id: str | None = None
    poligono: list[Ponto] = Field(default_factory=list)

    @field_validator("poligono")
    @classmethod
    def _poligono_valido(cls, v):
        return _validar_poligono(v)


class AtualizarZona(BaseModel):
    """Campos ausentes ficam como estao; poligono=[] remove a geometria."""
    nome: str | None = None
    descricao: str | None = None
    camera_id: str | None = None
    poligono: list[Ponto] | None = None
    ativa: bool | None = None

    @field_validator("poligono")
    @classmethod
    def _poligono_valido(cls, v):
        return _validar_poligono(v)
