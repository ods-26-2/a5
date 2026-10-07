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
