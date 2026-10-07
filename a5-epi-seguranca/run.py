"""
Executa o backend do A5 sem depender de venv, conda ou da variavel PYTHONPATH.

Por que este arquivo existe: em alguns laboratorios o ambiente Python (conda,
venv gerenciado, etc.) ignora a variavel de ambiente PYTHONPATH por algum
mecanismo de isolamento da maquina. Em vez de depender dela, este script
insere o caminho dos pacotes diretamente na lista `sys.path` do processo,
dentro do proprio Python - isso sempre funciona, independente do shell.

Uso:
    python3 run.py

Se voce instalou os pacotes em outro lugar (nao em ~/a5-libs), rode assim:
    python3 run.py /caminho/para/seus/pacotes
"""
import os
import sys

# 1) Descobre onde estao os pacotes instalados via `pip install --target=...`
if len(sys.argv) > 1:
    libs_dir = os.path.abspath(sys.argv[1])
else:
    libs_dir = os.path.expanduser("~/a5-libs")

if os.path.isdir(libs_dir):
    sys.path.insert(0, libs_dir)
else:
    print(
        f"[aviso] Pasta de pacotes '{libs_dir}' nao encontrada. "
        f"Se voce instalou em outro lugar, rode: python3 run.py /caminho/certo\n"
        f"Tentando importar mesmo assim, com o que ja estiver disponivel...",
        file=sys.stderr,
    )

# 2) Garante que a raiz do projeto (onde este arquivo esta) tambem esta no path,
#    para o "import src.a5..." funcionar independente de onde o comando roda.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 3) So agora importa uvicorn e o app - depois do sys.path ja estar corrigido.
try:
    import uvicorn
except ModuleNotFoundError:
    print(
        f"[erro] uvicorn nao foi encontrado em '{libs_dir}' nem no ambiente padrao.\n"
        f"Rode antes: pip install --target={libs_dir} -r requirements.txt\n",
        file=sys.stderr,
    )
    print("----- diagnostico -----", file=sys.stderr)
    print(f"Executavel Python em uso : {sys.executable}", file=sys.stderr)
    print(f"Versao do Python         : {sys.version.splitlines()[0]}", file=sys.stderr)
    print(f"Pasta de libs esperada   : {libs_dir}", file=sys.stderr)
    print(f"Pasta existe?            : {os.path.isdir(libs_dir)}", file=sys.stderr)
    if os.path.isdir(libs_dir):
        conteudo = sorted(os.listdir(libs_dir))
        tem_uvicorn = any(item.startswith("uvicorn") for item in conteudo)
        print(f"Tem algo com nome 'uvicorn' dentro? : {tem_uvicorn}", file=sys.stderr)
        print(f"Primeiros itens da pasta : {conteudo[:15]}", file=sys.stderr)
    print("------------------------", file=sys.stderr)
    print(
        "Se 'Tem algo com nome uvicorn' for True mas o import ainda falha,\n"
        "o pip usado para instalar e o 'python3' usado para rodar sao versoes\n"
        "diferentes do Python. Confirme rodando:\n"
        "  which python3 && which pip && python3 --version && pip --version",
        file=sys.stderr,
    )
    raise

from src.a5.main import app  # noqa: E402  (import depois do sys.path de proposito)

if __name__ == "__main__":
    print(f"Pacotes carregados de: {libs_dir}")
    print("Abrindo em http://localhost:8000  (docs em http://localhost:8000/docs)")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
