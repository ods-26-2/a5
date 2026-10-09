import { describe, expect, it } from 'vitest';
import { ignorarCliqueNaoPrimario, pontosSvg, poligonoUnico, resolverEpi, timelineDaOcorrencia, urlDoVideo } from './b6';
import type { EPI, Ocorrencia } from '../types';

const oc = (extra: Partial<Ocorrencia> = {}): Ocorrencia => ({
  alerta_id: 'a1', zona_id: 'z', pessoa_id: 'p1', epi: 'capacete', severidade: 'alta', descricao: '',
  evidencia_url: null, evidencia_inicio_seg: 1, evidencia_fim_seg: 6, em_violacao_ha_segundos: 30,
  deteccoes: [{ label: 'pessoa', x: 0.1, y: 0.2, width: 0.3, height: 0.4 }], ...extra,
});

describe('timelineDaOcorrencia', () => {
  it('converte deteccoes em um intervalo com caixas normalizadas', () => {
    const [t] = timelineDaOcorrencia(oc());
    expect(t.startTime).toBe(1);
    expect(t.endTime).toBe(6);
    expect(t.boxes).toHaveLength(1);
    expect(t.boxes[0]).toMatchObject({ x: 0.1, y: 0.2, width: 0.3, height: 0.4, label: 'p1 · capacete' });
  });
  it('sem deteccoes nao ha overlay', () => {
    expect(timelineDaOcorrencia(oc({ deteccoes: [] }))).toEqual([]);
  });
  it('sem fim definido o intervalo vai ate o fim do video', () => {
    expect(timelineDaOcorrencia(oc({ evidencia_inicio_seg: null, evidencia_fim_seg: null }))[0])
      .toMatchObject({ startTime: 0, endTime: Number.MAX_SAFE_INTEGER });
  });
});

describe('urlDoVideo', () => {
  it('troca a URL mock do S4 pelo video de demonstracao', () => {
    expect(urlDoVideo('https://s4.mock.local/e/1.mp4', 'demo.mp4')).toEqual({ src: 'demo.mp4', simulado: true });
  });
  it('mantem URLs reais e trata ausencia', () => {
    expect(urlDoVideo('https://s4.real.com/e/1.mp4', 'demo.mp4')).toEqual({ src: 'https://s4.real.com/e/1.mp4', simulado: false });
    expect(urlDoVideo(null, 'demo.mp4')).toEqual({ src: null, simulado: false });
  });
});

describe('poligonoUnico', () => {
  const zona = { zone_id: 'z', name: 'n', type: 't', points: [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }] };
  it('sem desenho devolve null (mantem o poligono atual)', () => expect(poligonoUnico([])).toBeNull());
  it('uma zona devolve os pontos', () => expect(poligonoUnico([zona])).toEqual(zona.points));
  it('mais de uma zona e erro', () => expect(() => poligonoUnico([zona, zona])).toThrow(/apenas uma zona/));
});

describe('resolverEpi', () => {
  const catalogo: EPI[] = [
    { id: 'capacete', nome: 'Capacete', ativo: true, aliases: ['helmet'] },
    { id: 'oculos', nome: 'Óculos de proteção', ativo: true, aliases: [] },
  ];
  it('resolve id, alias, nome e ignora caixa/acento', () => {
    expect(resolverEpi('HELMET', catalogo)).toBe('capacete');
    expect(resolverEpi('oculos de protecao', catalogo)).toBe('oculos');
    expect(resolverEpi('foguete', catalogo)).toBeNull();
  });
});

describe('pontosSvg', () => {
  it('converte [0,1] em viewBox 0-100', () => {
    expect(pontosSvg([{ x: 0.5, y: 0.25 }])).toBe('50.00,25.00');
  });
});

describe('ignorarCliqueNaoPrimario', () => {
  it('descarta mousedown do botao direito antes de chegar ao canvas, mas deixa o esquerdo passar', () => {
    const host = document.createElement('div');
    const canvas = document.createElement('canvas');
    host.appendChild(canvas);
    ignorarCliqueNaoPrimario(host);
    const botoes: number[] = [];
    canvas.addEventListener('mousedown', (e) => botoes.push(e.button));
    canvas.dispatchEvent(new MouseEvent('mousedown', { button: 0, bubbles: true }));
    canvas.dispatchEvent(new MouseEvent('mousedown', { button: 2, bubbles: true }));
    expect(botoes).toEqual([0]);
  });
});
