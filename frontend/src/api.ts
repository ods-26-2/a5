import { encerrarSessao, token } from './session';
import type {
  Alerta, AtualizarEPI, AtualizarUsuario, AtualizarZona, EPI, EstadoItem, FiltroHistorico, NovaPolitica,
  NovaZona, NovoEPI, NovoUsuario, Ocorrencia, Papel, Politica, Registro, Relatorio, Saude, SessaoApi,
  Turno, Usuario, ZonaCadastro,
} from './types';

const BASE = '/api';

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

/** FastAPI devolve `detail` como texto (HTTPException) ou lista (validacao do pydantic). */
export function mensagemDeErro(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const onde = Array.isArray(d?.loc) ? d.loc.filter((p: unknown) => p !== 'body').join('.') : '';
        return onde ? `${onde}: ${d?.msg ?? ''}` : String(d?.msg ?? '');
      })
      .join('; ');
  }
  return fallback;
}

let aoExpirar: () => void = () => {};
/** A tela principal registra o que fazer quando o backend responde 401 com sessão ativa. */
export const definirAoExpirar = (fn: () => void) => { aoExpirar = fn; };

async function fetchAutenticado(path: string, init?: RequestInit): Promise<Response> {
  const t = token();
  let resp: Response;
  try {
    resp = await fetch(BASE + path, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(t ? { Authorization: `Bearer ${t}` } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError('Não foi possível falar com o backend A5 (ele está rodando em :8000?).', 0);
  }
  if (!resp.ok) {
    let detail: unknown;
    try { detail = (await resp.json()).detail; } catch { /* corpo sem JSON */ }
    if (resp.status === 401 && t) {
      encerrarSessao();
      aoExpirar();
    }
    throw new ApiError(mensagemDeErro(detail, `Erro ${resp.status}`), resp.status);
  }
  return resp;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return (await fetchAutenticado(path, init)).json() as Promise<T>;
}

const send = <T>(method: string, path: string, body?: unknown) =>
  request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
const post = <T>(path: string, body?: unknown) => send<T>('POST', path, body);
const put = <T>(path: string, body: unknown) => send<T>('PUT', path, body);
const patch = <T>(path: string, body: unknown) => send<T>('PATCH', path, body);
const del = <T>(path: string) => send<T>('DELETE', path);
const enc = encodeURIComponent;

export const q = (params: Record<string, string | undefined>) => {
  const s = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]);
  return s.size ? `?${s}` : '';
};

const paramsHistorico = (f: FiltroHistorico) =>
  q({ zona_id: f.zona, usuario: f.usuario, tipo: f.tipo, desde: f.desde, ate: f.ate });

/** Baixa um arquivo (CSV) com a sessão e dispara o download no navegador. */
async function baixar(path: string, nome: string): Promise<void> {
  const blob = await (await fetchAutenticado(path)).blob();
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: nome });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const api = {
  saude: () => request<Saude>('/health'),

  // --- acesso ---
  login: (id: string, senha: string) => post<SessaoApi>('/auth/login', { id, senha }),
  logout: () => post<unknown>('/auth/logout'),
  eu: () => request<Usuario>('/auth/eu'),
  usuarios: () => request<Usuario[]>('/usuarios'),
  criarUsuario: (u: NovoUsuario) => post<Usuario>('/usuarios', u),
  atualizarUsuario: (id: string, d: AtualizarUsuario) => patch<Usuario>(`/usuarios/${enc(id)}`, d),

  // --- zonas e turnos ---
  zonas: (inativas = false) => request<ZonaCadastro[]>(`/zonas${inativas ? '?incluir_inativas=true' : ''}`),
  criarZona: (z: NovaZona) => post<ZonaCadastro>('/zonas', z),
  atualizarZona: (id: string, d: AtualizarZona) => put<ZonaCadastro>(`/zonas/${enc(id)}`, d),
  desativarZona: (id: string) => del<ZonaCadastro>(`/zonas/${enc(id)}`),
  /** Só vale para zona sem política e sem histórico; senão o backend responde 409. */
  apagarZona: (id: string) => del<{ status: string }>(`/zonas/${enc(id)}?definitivo=true`),
  turnos: (zona: string) => request<Turno[]>(`/monitoramento/zonas/${enc(zona)}/turnos`),
  salvarTurnos: (zona: string, t: Turno[]) => put<Turno[]>(`/monitoramento/zonas/${enc(zona)}/turnos`, t),
  monitoramentoAtivo: (zona: string) => request<{ ativo: boolean }>(`/monitoramento/zonas/${enc(zona)}/ativo`),

  // --- EPIs ---
  epis: () => request<EPI[]>('/catalogo/epis'),
  criarEpi: (e: NovoEPI) => post<EPI>('/catalogo/epis', e),
  atualizarEpi: (id: string, d: AtualizarEPI) => put<EPI>(`/catalogo/epis/${enc(id)}`, d),

  // --- politicas ---
  politicasVigentes: () => request<Politica[]>('/politica'),
  politicaVigente: (zona: string) => request<Politica>(`/politica/zonas/${enc(zona)}`),
  versoes: (zona: string) => request<Politica[]>(`/politica/zonas/${enc(zona)}/versoes`),
  definirPolitica: (zona: string, corpo: NovaPolitica) => post<Politica>(`/politica/zonas/${enc(zona)}`, corpo),

  // --- supervisao ---
  ocorrencias: (zona?: string) => request<Ocorrencia[]>(`/supervisao/ocorrencias${q({ zona_id: zona })}`),
  alertas: (zona?: string) => request<Alerta[]>(`/alertas${q({ zona_id: zona })}`),
  estadoDaZona: (zona: string) => request<EstadoItem[]>(`/alertas/zonas/${enc(zona)}/estado`),
  // Com sessão, o backend usa o usuário/papel do token e ignora o que vai no corpo.
  reconhecer: (id: string, usuario: string) => post<unknown>(`/alertas/${id}/ack`, { usuario }),
  silenciar: (id: string, usuario: string) => post<unknown>(`/alertas/${id}/mute`, { usuario }),
  desligar: (id: string, usuario: string, papel: Papel, motivo?: string) =>
    post<unknown>(`/alertas/${id}/desligar`, { usuario, papel, motivo: motivo || null }),

  // --- historico ---
  historico: (f: FiltroHistorico = {}) => request<Registro[]>(`/historico${paramsHistorico(f)}`),
  relatorio: (zona: string, f: Pick<FiltroHistorico, 'desde' | 'ate'> = {}) =>
    request<Relatorio>(`/historico/relatorio/${enc(zona)}${q({ desde: f.desde, ate: f.ate })}`),
  exportarHistorico: (f: FiltroHistorico = {}) => baixar(`/historico/exportar${paramsHistorico(f)}`, 'historico-a5.csv'),
  exportarRelatorio: (zona: string, f: Pick<FiltroHistorico, 'desde' | 'ate'> = {}) =>
    baixar(`/historico/relatorio/${enc(zona)}/exportar${q({ desde: f.desde, ate: f.ate })}`, `relatorio-${zona}.csv`),
};
