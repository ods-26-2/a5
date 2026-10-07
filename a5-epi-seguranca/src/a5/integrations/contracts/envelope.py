"""
Envelope comum definido pela frente B1 (origem, horario, confianca, versao).

Este e um MODELO ASSUMIDO para desenvolvimento local. Quando B1 publicar o
schema oficial, substituir os campos aqui e re-gerar os mocks que o usam.
"""
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
