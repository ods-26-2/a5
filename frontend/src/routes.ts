import type { Papel } from './types';
import { ehAdministrador, podeConfigurar, podeVerRelatorios } from './session';

export interface RotaInfo { titulo: string; visivel: (p: Papel) => boolean }

/** Quais telas cada papel enxerga no menu (o backend continua sendo quem autoriza). */
export const ROTAS: Record<string, RotaInfo> = {
  '/supervisao': { titulo: 'Supervisão', visivel: () => true },
  '/zonas': { titulo: 'Zonas', visivel: () => true },
  '/politicas': { titulo: 'Políticas', visivel: () => true },
  '/epis': { titulo: 'EPIs', visivel: () => true },
  '/historico': { titulo: 'Histórico', visivel: podeVerRelatorios },
  '/usuarios': { titulo: 'Usuários', visivel: ehAdministrador },
};

export const rotasVisiveis = (papel: Papel): string[] =>
  Object.entries(ROTAS).filter(([, r]) => r.visivel(papel)).map(([path]) => path);

/** Rota pedida -> rota que o papel pode abrir (cai na Supervisão se nao puder). */
export function rotaPermitida(path: string, papel: Papel): string {
  return ROTAS[path] && ROTAS[path].visivel(papel) ? path : '/supervisao';
}

export { podeConfigurar };
