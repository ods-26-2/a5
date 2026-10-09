"""
RF9 - usuarios, login e sessoes (em memoria).

Senhas ficam como hash PBKDF2 com sal. Sessoes sao tokens aleatorios com validade.
E simples de proposito: trocar por SSO/Supabase Auth mantendo `identidade()` e
`exigir_papel()` (auth/deps.py) como unica porta de entrada na API.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from src.a5.auth.models import AtualizarUsuario, NovoUsuario, Usuario
from src.a5.auth.permissions import Papel

_ITERACOES = 120_000
VALIDADE_SESSAO = timedelta(hours=8)


def _hash(senha: str, sal: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, _ITERACOES).hex()


class AuthService:
    def __init__(self):
        self._usuarios: dict[str, Usuario] = {}
        self._senhas: dict[str, tuple[bytes, str]] = {}
        self._sessoes: dict[str, tuple[str, datetime]] = {}

    # --- usuarios ---
    def listar(self) -> list[Usuario]:
        return list(self._usuarios.values())

    def obter(self, usuario_id: str) -> Usuario | None:
        return self._usuarios.get(usuario_id)

    def _definir_senha(self, usuario_id: str, senha: str) -> None:
        if len(senha) < 4:
            raise ValueError("A senha precisa de pelo menos 4 caracteres.")
        sal = secrets.token_bytes(16)
        self._senhas[usuario_id] = (sal, _hash(senha, sal))

    def cadastrar(self, novo: NovoUsuario) -> Usuario:
        existente = self._usuarios.get(novo.id)
        if existente is not None:
            raise ValueError(f"O usuario '{novo.id}' ja existe.")
        if novo.senha is not None:
            self._definir_senha(novo.id, novo.senha)
        usuario = Usuario(id=novo.id, nome=novo.nome, papel=novo.papel)
        self._usuarios[usuario.id] = usuario
        return usuario

    def atualizar(self, usuario_id: str, dados: AtualizarUsuario) -> Usuario:
        atual = self._usuarios.get(usuario_id)
        if atual is None:
            raise LookupError(f"Usuario '{usuario_id}' nao encontrado.")
        campos = dados.model_dump(exclude_none=True, exclude={"senha"})
        novo = atual.model_copy(update=campos)
        if atual.papel == Papel.ADMINISTRADOR and (
            novo.papel != Papel.ADMINISTRADOR or not novo.ativo
        ):
            outros = [
                u for u in self._usuarios.values()
                if u.id != usuario_id and u.papel == Papel.ADMINISTRADOR and u.ativo
            ]
            if not outros:
                raise ValueError("Precisa existir pelo menos um administrador ativo.")
        if dados.senha is not None:
            self._definir_senha(usuario_id, dados.senha)
        self._usuarios[usuario_id] = novo
        if not novo.ativo:
            self._encerrar_sessoes(usuario_id)
        return novo

    # --- sessoes ---
    def login(self, usuario_id: str, senha: str) -> tuple[str, Usuario] | None:
        usuario = self._usuarios.get(usuario_id)
        registro = self._senhas.get(usuario_id)
        if usuario is None or registro is None or not usuario.ativo:
            return None
        sal, esperado = registro
        if not hmac.compare_digest(_hash(senha, sal), esperado):
            return None
        token = secrets.token_urlsafe(32)
        self._sessoes[token] = (usuario_id, datetime.now(timezone.utc) + VALIDADE_SESSAO)
        return token, usuario

    def usuario_do_token(self, token: str) -> Usuario | None:
        sessao = self._sessoes.get(token)
        if sessao is None:
            return None
        usuario_id, expira = sessao
        usuario = self._usuarios.get(usuario_id)
        if expira < datetime.now(timezone.utc) or usuario is None or not usuario.ativo:
            self._sessoes.pop(token, None)
            return None
        return usuario

    def logout(self, token: str) -> None:
        self._sessoes.pop(token, None)

    def _encerrar_sessoes(self, usuario_id: str) -> None:
        for token in [t for t, (u, _) in self._sessoes.items() if u == usuario_id]:
            del self._sessoes[token]


_auth_singleton: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_singleton
    if _auth_singleton is None:
        _auth_singleton = AuthService()
        _semear(_auth_singleton)
    return _auth_singleton


def _semear(auth: AuthService) -> None:
    """Usuarios iniciais. Em desenvolvimento cria um de cada papel (senha = id + '123');
    fora dele, so o administrador, e a senha vem de A5_ADMIN_SENHA."""
    from src.a5.config import settings

    if settings.env == "development":
        for papel in Papel:
            auth.cadastrar(NovoUsuario(
                id=papel.value, nome=papel.value.capitalize(), papel=papel,
                senha=(settings.admin_senha or "admin123") if papel == Papel.ADMINISTRADOR else f"{papel.value}123",
            ))
    elif settings.admin_senha:
        auth.cadastrar(NovoUsuario(
            id="administrador", nome="Administrador", papel=Papel.ADMINISTRADOR,
            senha=settings.admin_senha,
        ))
