import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Ponto(BaseModel):
    """Vertice do poligono da zona, em coordenadas normalizadas [0.0, 1.0] (formato do B6)."""
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)


class Zona(BaseModel):
    id: str
    nome: str | None = None
    # V6/S1: toda zona declara seu sistema de coordenadas. O editor B6 exporta
    # coordenadas normalizadas [0,1] relativas ao quadro da camera.
    espaco_coordenadas: Literal["imagem_normalizada"] = "imagem_normalizada"
    # Vazio = zona so por id (sem geometria). Com geometria, minimo 3 pontos.
    poligono: list[Ponto] = Field(default_factory=list)

    @field_validator("poligono")
    @classmethod
    def _poligono_valido(cls, pontos: list[Ponto]) -> list[Ponto]:
        if pontos and len(pontos) < 3:
            raise ValueError("O poligono da zona precisa de pelo menos 3 pontos.")
        return pontos


class EquipamentoExigido(BaseModel):
    epi_id: str  # id, nome ou alias; o service converte para o id canonico
    # None = herda o padrao da politica.
    tempo_tolerancia_segundos: int | None = Field(None, ge=0)
    confianca_minima: float | None = Field(None, ge=0.0, le=1.0)


class NovaPolitica(BaseModel):
    """Corpo de criacao. Cada POST gera uma nova versao da politica da zona."""
    id: str | None = None  # slug (ex.: "obra-civil-sp"); padrao: "politica-<zona>"
    zona: Zona
    classe_pessoa: str = "pessoa"
    equipamentos_obrigatorios: list[EquipamentoExigido] = Field(..., min_length=1)
    # Padroes da politica, usados pelos equipamentos que nao definem os seus.
    tempo_tolerancia_segundos: int = Field(10, ge=0)
    confianca_minima: float = Field(0.6, ge=0.0, le=1.0)

    @field_validator("equipamentos_obrigatorios", mode="before")
    @classmethod
    def _aceita_lista_de_nomes(cls, valor):
        # ["capacete", "colete"] vira [{"epi_id": "capacete"}, {"epi_id": "colete"}]
        if isinstance(valor, list):
            return [{"epi_id": v} if isinstance(v, str) else v for v in valor]
        return valor


class RequisitoEfetivo(BaseModel):
    """Equipamento exigido ja com tolerancia e confianca resolvidas."""
    epi_id: str
    tempo_tolerancia_segundos: int
    confianca_minima: float


class PoliticaViolacao(BaseModel):
    id: str
    versao: int
    zona: Zona
    classe_pessoa: str
    equipamentos_obrigatorios: list[EquipamentoExigido]
    tempo_tolerancia_segundos: int
    confianca_minima: float
    criada_em: datetime

    def requisitos(self) -> list[RequisitoEfetivo]:
        return [
            RequisitoEfetivo(
                epi_id=e.epi_id,
                tempo_tolerancia_segundos=(
                    self.tempo_tolerancia_segundos
                    if e.tempo_tolerancia_segundos is None
                    else e.tempo_tolerancia_segundos
                ),
                confianca_minima=(
                    self.confianca_minima if e.confianca_minima is None else e.confianca_minima
                ),
            )
            for e in self.equipamentos_obrigatorios
        ]


_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Turno(BaseModel):
    """RF12 - horarios de monitoramento ativo por zona."""
    zona_id: str = ""
    inicio: str  # "HH:MM"
    fim: str  # "HH:MM"; menor que o inicio = cruza a meia-noite

    @field_validator("inicio", "fim")
    @classmethod
    def _hora_valida(cls, v: str) -> str:
        if not _HHMM.match(v):
            raise ValueError("Use o formato HH:MM (00:00 a 23:59).")
        return v

    @model_validator(mode="after")
    def _intervalo_valido(self):
        if self.inicio == self.fim:
            raise ValueError("Inicio e fim nao podem ser iguais.")
        return self

    def minutos(self) -> tuple[int, int]:
        h1, m1 = map(int, self.inicio.split(":"))
        h2, m2 = map(int, self.fim.split(":"))
        return h1 * 60 + m1, h2 * 60 + m2
