/**
 * Cola entre o kit B6 (vendor/b6, intocado) e os modelos do A5.
 * Tudo aqui e funcao pura para ser testavel sem DOM.
 */
import type { FrameIntervalMetadata } from '../../vendor/b6/b6-overlay-player/b6_overlay_player';
import type { ZonePayload } from '../../vendor/b6/b6-zone-editor/b6_zone_editor';
import type { EPI, Ocorrencia, Ponto, Severidade } from '../types';

export const COR_SEVERIDADE: Record<Severidade, string> = {
  baixa: '#7dd3fc',
  media: '#facc15',
  alta: '#fb923c',
  critica: '#f87171',
};

/** Ocorrencia (S3 + S4) -> linha do tempo do OverlayPlayer. Sem deteccoes, nao ha overlay. */
export function timelineDaOcorrencia(o: Ocorrencia): FrameIntervalMetadata[] {
  if (o.deteccoes.length === 0) return [];
  return [
    {
      startTime: o.evidencia_inicio_seg ?? 0,
      endTime: o.evidencia_fim_seg ?? Number.MAX_SAFE_INTEGER,
      boxes: o.deteccoes.map((d, i) => ({
        id: `${o.alerta_id}-${i}`,
        label: `${o.pessoa_id} · ${o.epi}`,
        color: COR_SEVERIDADE[o.severidade] ?? '#f87171',
        x: d.x, y: d.y, width: d.width, height: d.height,
      })),
    },
  ];
}

/** A URL mock do S4 (https://s4.mock.local/...) nao resolve; usa um video de demonstracao. */
export function urlDoVideo(url: string | null, demo: string): { src: string | null; simulado: boolean } {
  if (!url) return { src: null, simulado: false };
  try {
    if (new URL(url).hostname.endsWith('.mock.local')) return { src: demo, simulado: true };
  } catch { /* URL relativa ou invalida: usa como veio */ }
  return { src: url, simulado: false };
}

/** Saida do ZoneEditor -> poligono unico da politica (uma politica = uma zona). */
export function poligonoUnico(zonas: ZonePayload[]): Ponto[] | null {
  if (zonas.length === 0) return null;
  if (zonas.length > 1) {
    throw new Error(`Desenhe apenas uma zona por política (há ${zonas.length} no editor).`);
  }
  return zonas[0].points.map(({ x, y }) => ({ x, y }));
}

const norm = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim().replace(/\s+/g, ' ');

/** Mesma regra do backend (CatalogoEPIService.resolver_epi): id, nome ou alias. */
export function resolverEpi(nome: string, catalogo: EPI[]): string | null {
  const chave = norm(nome);
  const achado = catalogo.find((e) => [e.id, e.nome, ...e.aliases].some((n) => norm(n) === chave));
  return achado?.id ?? null;
}

export function pontosSvg(poligono: Ponto[]): string {
  return poligono.map((p) => `${(p.x * 100).toFixed(2)},${(p.y * 100).toFixed(2)}`).join(' ');
}

/**
 * Workaround para o ZoneEditor (B6.2): o handler de `mousedown` nao filtra o botao,
 * entao o clique direito (que so deveria fechar o poligono) antes adiciona um ponto.
 * Um listener em captura no contentor descarta tudo que nao for botao esquerdo, sem
 * mexer no codigo do B6. `contextmenu` continua chegando ao editor normalmente.
 * Remover quando o B6 corrigir (checar `e.button === 0` em onMouseDown).
 */
export function ignorarCliqueNaoPrimario(host: HTMLElement): void {
  host.addEventListener('mousedown', (e) => { if (e.button !== 0) e.stopPropagation(); }, true);
}
