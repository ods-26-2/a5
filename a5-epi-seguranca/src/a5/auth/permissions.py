"""
RF9 - Perfis de acesso (Operador, Supervisor, Auditor) com permissoes granulares.

Comeca simples (enum + funcoes puras) de proposito: e facil de testar e de trocar
por um esquema mais robusto (RBAC com banco) depois, sem afetar quem ja usa
`usuario_pode_desligar_alarme` etc.
"""
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
