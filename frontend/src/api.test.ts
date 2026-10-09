import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, definirAoExpirar, q } from './api';
import { encerrarSessao, iniciarSessao, temSessao, token } from './session';

const resposta = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { 'Content-Type': 'application/json' } });

beforeEach(() => encerrarSessao());
afterEach(() => vi.restoreAllMocks());

describe('api', () => {
  it('envia o token Bearer da sessão', async () => {
    iniciarSessao('tok-123', { id: 'ana', nome: 'Ana', papel: 'supervisor', ativo: true });
    const f = vi.spyOn(globalThis, 'fetch').mockResolvedValue(resposta([]));
    await api.zonas();
    const init = f.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok-123');
    expect(f.mock.calls[0][0]).toBe('/api/zonas');
  });

  it('sem sessão não manda Authorization', async () => {
    const f = vi.spyOn(globalThis, 'fetch').mockResolvedValue(resposta({ token: 't', usuario: {} }));
    await api.login('a', 'b');
    const init = f.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBeUndefined();
    expect(init.method).toBe('POST');
  });

  it('401 com sessão encerra a sessão e avisa a tela', async () => {
    iniciarSessao('velho', { id: 'ana', nome: 'Ana', papel: 'operador', ativo: true });
    const expirou = vi.fn();
    definirAoExpirar(expirou);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(resposta({ detail: 'Sessao invalida ou expirada.' }, 401));
    await expect(api.zonas()).rejects.toMatchObject({ status: 401, message: 'Sessao invalida ou expirada.' });
    expect(expirou).toHaveBeenCalledOnce();
    expect(temSessao()).toBe(false);
    expect(token()).toBeNull();
  });

  it('401 de login errado (sem sessão) não dispara expiração', async () => {
    const expirou = vi.fn();
    definirAoExpirar(expirou);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(resposta({ detail: 'Usuario ou senha invalidos.' }, 401));
    await expect(api.login('x', 'y')).rejects.toBeInstanceOf(ApiError);
    expect(expirou).not.toHaveBeenCalled();
  });

  it('zona: PUT com polígono vazio e DELETE usam o caminho certo', async () => {
    const f = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => resposta({}));
    await api.atualizarZona('z 1', { poligono: [] });
    await api.desativarZona('z 1');
    expect(f.mock.calls[0][0]).toBe('/api/zonas/z%201');
    expect((f.mock.calls[0][1] as RequestInit).method).toBe('PUT');
    expect((f.mock.calls[0][1] as RequestInit).body).toBe('{"poligono":[]}');
    expect((f.mock.calls[1][1] as RequestInit).method).toBe('DELETE');
    await api.apagarZona('z 1');
    expect(f.mock.calls[2][0]).toBe('/api/zonas/z%201?definitivo=true');
  });

  it('q monta a query sem parâmetros vazios', () => {
    expect(q({ a: '1', b: undefined, c: '' })).toBe('?a=1');
    expect(q({})).toBe('');
  });
});
