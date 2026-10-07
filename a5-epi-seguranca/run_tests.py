"""
Roda os testes sem depender de PYTHONPATH (mesmo motivo do run.py - ver esse
arquivo para a explicacao completa).

Uso:
    python3 run_tests.py
    python3 run_tests.py /caminho/para/seus/pacotes   (se nao usou ~/a5-libs)
"""
import os
import sys

if len(sys.argv) > 1:
    libs_dir = os.path.abspath(sys.argv[1])
else:
    libs_dir = os.path.expanduser("~/a5-libs")

if os.path.isdir(libs_dir):
    sys.path.insert(0, libs_dir)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q"]))
