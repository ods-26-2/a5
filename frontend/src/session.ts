import type { Papel, Usuario } from './types';

export interface Sessao { usuario: string; nome: string; papel: Papel; token: string }

const CHAVE = 'a5.sessao';
let atual: Sessao | null = carregar();

function carregar(): Sessao | null {
  try {
    const bruto = localStorage.getItem(CHAVE);
    if (bruto) {
      const s = JSON.parse(bruto) as Sessao;
      if (s?.token && s?.usuario && s?.papel) return s;
    }
  } catch { /* storage indisponivel */ }
  return null;
}

export const temSessao = (): boolean => atual !== null;
export const token = (): string | null => atual?.token ?? null;

/** Sessao do usuario logado. So chamar de telas montadas depois do login. */
export function sessao(): Sessao {
  if (!atual) throw new Error('Sem sessão: faça login.');
  return atual;
}

export function iniciarSessao(tokenApi: string, u: Usuario): void {
  atual = { token: tokenApi, usuario: u.id, nome: u.nome, papel: u.papel };
  try { localStorage.setItem(CHAVE, JSON.stringify(atual)); } catch { /* ignora */ }
}

export function encerrarSessao(): void {
  atual = null;
  try { localStorage.removeItem(CHAVE); } catch { /* ignora */ }
}

// Espelho de src/a5/auth/permissions.py, so para habilitar/desabilitar botoes e menus.
// Quem decide de verdade e o backend (403).
export const podeDesligar = (p: Papel) => p === 'supervisor' || p === 'administrador';
export const podeConfigurar = (p: Papel) => p === 'supervisor' || p === 'administrador';
export const podeVerRelatorios = (p: Papel) => p === 'supervisor' || p === 'auditor' || p === 'administrador';
export const ehAdministrador = (p: Papel) => p === 'administrador';
