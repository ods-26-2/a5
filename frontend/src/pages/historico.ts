import { api } from '../api';
import type { FiltroHistorico, Registro, Relatorio } from '../types';
import { urlDoVideo } from '../adapters/b6';
import { append, dataHora, fimDoDia, h, inicioDoDia, limpar, toast } from '../ui';

const ROTULO: Record<Registro['tipo'], string> = { ack: 'Reconhecimento', mute: 'Silenciamento', desligamento: 'Desligamento' };

export function paginaHistorico(root: HTMLElement): () => void {
  const recarregar = () => void Promise.all([carregar(), relatorio()]);
  // Cada mudança de filtro dispara uma busca; só a mais recente pode desenhar,
  // senão uma resposta antiga que chega depois sobrescreve a nova.
  let seqTabela = 0;
  let seqRelatorio = 0;

  const filtroZona = h('select', { onchange: recarregar }, h('option', { value: '' }, 'Todas as zonas'));
  const filtroUsuario = h('input', { type: 'text', placeholder: 'ex.: supervisor.joana', onchange: recarregar });
  const filtroTipo = h('select', { onchange: recarregar },
    h('option', { value: '' }, 'Todas as ações'),
    ...Object.entries(ROTULO).map(([v, t]) => h('option', { value: v }, t)));
  const filtroDe = h('input', { type: 'date', onchange: recarregar });
  const filtroAte = h('input', { type: 'date', onchange: recarregar });
  const tabela = h('div', null);
  const cartaoRelatorio = h('div', { class: 'relatorio' });

  const filtros = (): FiltroHistorico => ({
    zona: filtroZona.value || undefined,
    usuario: filtroUsuario.value.trim() || undefined,
    tipo: filtroTipo.value || undefined,
    desde: inicioDoDia(filtroDe.value),
    ate: fimDoDia(filtroAte.value),
  });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'Histórico'), h('p', { class: 'sub' }, 'Ações humanas sobre alertas — auditoria de autor, horário, setor e evidência.')),
      h('div', { class: 'acoes' },
        h('button', { class: 'btn', onclick: () => void exportar(() => api.exportarHistorico(filtros())) }, 'Exportar histórico (CSV)'),
        h('button', { class: 'btn', onclick: () => void exportar(() => api.exportarRelatorio(zonaDoRelatorio(), filtros())) }, 'Exportar relatório (CSV)'))),
    h('section', { class: 'painel filtros' },
      h('label', { class: 'campo' }, 'Zona', filtroZona),
      h('label', { class: 'campo' }, 'Usuário', filtroUsuario),
      h('label', { class: 'campo' }, 'Ação', filtroTipo),
      h('label', { class: 'campo' }, 'De', filtroDe),
      h('label', { class: 'campo' }, 'Até', filtroAte)),
    h('div', { class: 'duas-colunas largura-igual' },
      h('section', { class: 'painel' }, h('h2', null, 'Ações registradas'), tabela),
      h('section', { class: 'painel' }, h('h2', null, 'Relatório da zona'), cartaoRelatorio)),
  );

  async function carregar() {
    const minha = ++seqTabela;
    limpar(tabela);
    try {
      const registros = (await api.historico(filtros())).slice().reverse();
      if (minha !== seqTabela) return;
      if (registros.length === 0) {
        tabela.append(h('p', { class: 'vazio' }, 'Nenhuma ação registrada com esses filtros.'));
        return;
      }
      tabela.append(
        h('table', { class: 'tabela' },
          h('thead', null, h('tr', null, ...['Quando', 'Usuário', 'Ação', 'Zona', 'Alerta', 'Evidência'].map((t) => h('th', null, t)))),
          h('tbody', null, ...registros.map((r) =>
            h('tr', null,
              h('td', null, dataHora(r.registrado_em)),
              h('td', { class: 'mono' }, r.usuario),
              h('td', null, h('span', { class: `chip acao-${r.tipo}` }, ROTULO[r.tipo])),
              h('td', { class: 'mono' }, r.zona_id ?? '—'),
              h('td', { class: 'mono' }, r.alerta_id),
              h('td', null, evidencia(r.evidencia_url)))))),
      );
    } catch (e) {
      if (minha === seqTabela) tabela.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  /** Link da evidência (S4). Com o S4 em mock a URL não existe, então só sinaliza. */
  function evidencia(url: string | null) {
    if (!url) return '—';
    if (urlDoVideo(url, '').simulado) return h('span', { class: 'chip', title: url }, 'simulada');
    return h('a', { href: url, target: '_blank', rel: 'noopener' }, 'abrir');
  }

  const zonaDoRelatorio = () => filtroZona.value || (filtroZona.options[1]?.value ?? '');

  async function exportar(baixar: () => Promise<void>) {
    try { await baixar(); } catch (e) { toast(e instanceof Error ? e.message : String(e), 'erro'); }
  }

  async function zonas() {
    try {
      const [cadastradas, alertas] = await Promise.all([api.zonas(true), api.alertas()]);
      const ids = [...new Set([...cadastradas.map((z) => z.id), ...alertas.map((a) => a.zona_id)])].sort();
      filtroZona.append(...ids.map((z) => h('option', { value: z }, z)));
    } catch { /* os filtros seguem funcionando sem a lista */ }
  }

  /** O relatório é por zona: usa a zona filtrada ou, sem filtro, a primeira conhecida. */
  async function relatorio() {
    const minha = ++seqRelatorio;
    limpar(cartaoRelatorio);
    const zona = zonaDoRelatorio();
    if (!zona) {
      cartaoRelatorio.append(h('p', { class: 'vazio' }, 'Sem zonas conhecidas.'));
      return;
    }
    try {
      const { desde, ate } = filtros();
      const r: Relatorio = await api.relatorio(zona, { desde, ate });
      if (minha !== seqRelatorio) return;
      append(cartaoRelatorio, [
        h('p', { class: 'meta mono' }, zona),
        h('p', { class: 'numero-grande' }, String(r.total), h('span', null, ' violações no período')),
        r.total > 0 && h('h3', null, 'Por severidade'),
        ...barras(r.por_severidade, 'sev'),
        r.total > 0 && h('h3', null, 'Por tipo de EPI'),
        ...barras(r.por_epi, 'epi'),
      ]);
    } catch (e) {
      if (minha === seqRelatorio) cartaoRelatorio.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function barras(dados: Record<string, number>, tipo: 'sev' | 'epi') {
    const max = Math.max(1, ...Object.values(dados));
    return Object.entries(dados).map(([nome, n]) =>
      h('div', { class: 'barra-linha' },
        tipo === 'sev' ? h('span', { class: `badge sev-${nome}` }, nome) : h('span', { class: 'chip' }, nome),
        h('div', { class: 'barra' }, h('div', { class: `barra-preench ${tipo === 'sev' ? `sev-${nome}` : 'epi'}`, style: `width:${(n / max) * 100}%` })),
        h('span', { class: 'mono' }, String(n))));
  }

  void zonas().then(recarregar);
  return () => {};
}
