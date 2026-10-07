from pydantic import BaseModel

from src.a5.auth.permissions import Papel


class Usuario(BaseModel):
    id: str
    nome: str
    papel: Papel
