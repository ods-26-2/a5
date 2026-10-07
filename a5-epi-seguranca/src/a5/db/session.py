"""
Ainda nao ha banco real: os repositories dos modulos guardam tudo em memoria
(dicionarios/listas em singletons no proprio modulo). Este arquivo existe como
o lugar unico para plugar SQLAlchemy/Postgres depois, sem espalhar a mudanca.
"""


def get_session():
    raise NotImplementedError(
        "Sem banco real ainda. Os repositories em src/a5/modules/*/repository.py "
        "usam armazenamento em memoria por enquanto (ver P3 / build da aplicacao)."
    )
