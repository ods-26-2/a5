import { describe, expect, it } from 'vitest';
import { rotaPermitida, rotasVisiveis } from './routes';

describe('rotas por papel', () => {
  it('operador não vê histórico nem usuários', () => {
    expect(rotasVisiveis('operador')).toEqual(['/supervisao', '/zonas', '/politicas', '/epis']);
  });
  it('auditor vê histórico mas não usuários', () => {
    const r = rotasVisiveis('auditor');
    expect(r).toContain('/historico');
    expect(r).not.toContain('/usuarios');
  });
  it('administrador vê tudo', () => {
    expect(rotasVisiveis('administrador')).toHaveLength(6);
  });
  it('rota proibida cai na supervisão; desconhecida também', () => {
    expect(rotaPermitida('/usuarios', 'supervisor')).toBe('/supervisao');
    expect(rotaPermitida('/nao-existe', 'administrador')).toBe('/supervisao');
    expect(rotaPermitida('/historico', 'supervisor')).toBe('/historico');
  });
});
