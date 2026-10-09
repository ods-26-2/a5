import { OverlayPlayer } from '../../vendor/b6/b6-overlay-player/b6_overlay_player';
import { resolverEpi, timelineDaOcorrencia, urlDoVideo } from '../adapters/b6';
import { api, ApiError } from '../api';
import { podeDesligar, sessao } from '../session';
import type { Alerta, EPI, EstadoItem, Ocorrencia, Politica, Severidade } from '../types';
import { append, dataHora, h, limpar, pct, toast } from '../ui';

const DEMO_VIDEO =
  (import.meta.env.VITE_DEMO_VIDEO as string | undefined) ?? 'https://www.w3schools.com/html/mov_bbb.mp4';
const PESO: Record<Severidade, number> = { critica: 4, alta: 3, media: 2, baixa: 1 };
const POLL_MS = 10_000;

export function paginaSupervisao(root: HTMLElement): () => void {
  let zona = '';
  let ocorrencias: Ocorrencia[] = [];
  let alertas = new Map<string, Alerta>();
  let politicas: Politica[] = [];
  let epis: EPI[] = [];
  let estado: EstadoItem[] = [];
  let selecionada: string | null = null;
  let desligando = false;
  const zonasConhecidas = new Set<string>();
  let seq = 0; // só a busca mais recente atualiza a tela (poll, filtro e ações se cruzam)

  const seletorZona = h('select', { onchange: () => { zona = seletorZona.value; void carregar(); } });
  const lista = h('div', { class: 'lista', role: 'list' });
  const painel = h('section', { class: 'painel detalhe' });
  const info = h('div', { class: 'detalhe-info' });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'Supervisão'), h('p', { class: 'sub' }, 'Violações de EPI em tempo quase real, com evidência.')),
      h('label', { class: 'campo inline' }, 'Zona', seletorZona),
    ),
    h('div', { class: 'duas-colunas' }, h('aside', { class: 'painel coluna-lista' }, lista), painel),
  );

  function opcoesDeZona() {
    limpar(seletorZona);
    seletorZona.append(h('option', { value: '' }, 'Todas as zonas'));
    for (const z of [...zonasConhecidas].sort()) {
      seletorZona.append(h('option', { value: z, selected: z === zona }, z));
    }
  }

  async function carregar() {
    const minha = ++seq;
    try {
      const [oc, al, po, ep] = await Promise.all([
        api.ocorrencias(zona || undefined),
        api.alertas(zona || undefined),
        api.politicasVigentes(),
        epis.length ? Promise.resolve(epis) : api.epis(),
      ]);
      if (minha !== seq) return;
      ocorrencias = oc.sort(
        (a, b) => PESO[b.severidade] - PESO[a.severidade] || a.alerta_id.localeCompare(b.alerta_id),
      );
      alertas = new Map(al.map((a) => [a.alerta_id, a]));
      politicas = po;
      epis = ep;
      oc.forEach((o) => zonasConhecidas.add(o.zona_id));
      po.forEach((p) => zonasConhecidas.add(p.zona.id));
      opcoesDeZona();
      renderLista();
      if (selecionada && !ocorrencias.some((o) => o.alerta_id === selecionada)) selecionada = null;
      if (selecionada) renderInfo();
      else renderVazio();
    } catch (e) {
      limpar(lista);
      lista.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function renderLista() {
    limpar(lista);
    if (ocorrencias.length === 0) {
      lista.append(h('p', { class: 'vazio' }, 'Nenhuma violação ativa.'));
      return;
    }
    for (const o of ocorrencias) {
      const a = alertas.get(o.alerta_id);
      lista.append(
        h('button', {
          class: `card-ocorrencia sev-${o.severidade}${o.alerta_id === selecionada ? ' ativo' : ''}`,
          role: 'listitem',
          onclick: () => void selecionar(o.alerta_id),
        },
          h('div', { class: 'linha' }, h('strong', null, o.epi), badge(o.severidade)),
          h('div', { class: 'meta mono' }, `${o.pessoa_id} · ${o.zona_id}`),
          h('div', { class: 'chips' },
            a?.reconhecido && h('span', { class: 'chip ok' }, 'reconhecido'),
            a?.silenciado && h('span', { class: 'chip mudo' }, 'silenciado'),
          ),
        ),
      );
    }
  }

  function renderVazio() {
    limpar(painel);
    painel.append(h('p', { class: 'vazio centro' }, 'Selecione uma ocorrência para ver a evidência.'));
  }

  async function selecionar(id: string) {
    selecionada = id;
    desligando = false;
    const o = ocorrencias.find((x) => x.alerta_id === id)!;
    estado = [];
    renderLista();
    limpar(painel);

    const host = h('div', { id: 'player-host' });
    const { src, simulado } = urlDoVideo(o.evidencia_url, DEMO_VIDEO);
    append(painel, [
      src ? host : h('div', { class: 'sem-video' }, 'Sem evidência de mídia para este alerta.'),
      simulado && h('p', { class: 'aviso' }, 'Evidência simulada (S4 em mock): exibindo vídeo de demonstração.'),
      info,
    ]);
    if (src) {
      const player = new OverlayPlayer({ containerId: 'player-host', videoUrl: src, autoPlay: false });
      player.loadMetadataTimeline(timelineDaOcorrencia(o));
    }
    renderInfo();
    try {
      estado = (await api.estadoDaZona(o.zona_id)).filter((e) => e.pessoa_id === o.pessoa_id);
      if (selecionada === id) renderInfo();
    } catch { /* o estado e complementar; segue sem ele */ }
  }

  function renderInfo() {
    const o = ocorrencias.find((x) => x.alerta_id === selecionada);
    if (!o) return;
    const a = alertas.get(o.alerta_id);
    const politica = politicas.find((p) => p.zona.id === o.zona_id);
    const violado = resolverEpi(o.epi, epis) ?? o.epi;
    const u = sessao();

    limpar(info);
    append(info, [
      h('div', { class: 'linha' }, h('h2', null, o.descricao), badge(o.severidade)),
      h('p', { class: 'meta mono' }, `${o.alerta_id}${a ? ' · ' + dataHora(a.criado_em) : ''}`),

      h('h3', null, 'Política da zona'),
      politica
        ? h('div', null,
            h('p', { class: 'meta' }, `${politica.id} · v${politica.versao} · exige:`),
            h('div', { class: 'chips' },
              ...politica.equipamentos_obrigatorios.map((e) =>
                h('span', { class: `chip${e.epi_id === violado ? ' alerta' : ''}` }, e.epi_id)),
            ))
        : h('p', { class: 'meta' }, 'Esta zona ainda não tem política. ', h('a', { href: '#/politicas' }, 'Definir')),

      estado.length > 0 && h('div', null,
        h('h3', null, `Estado de ${o.pessoa_id} (I9)`),
        h('table', { class: 'tabela' },
          h('tbody', null, ...estado.map((e) =>
            h('tr', null,
              h('td', null, e.epi),
              h('td', null, h('span', { class: `chip est-${e.estado}` }, e.estado)),
              h('td', { class: 'mono' }, pct(e.confianca)),
              h('td', null, e.classificacao === 'incerta' && h('span', { class: 'chip duvida', title: 'Confiança intermediária: o sistema não age sozinho, confirme visualmente.' }, 'dúvida')))))),
      ),

      h('div', { class: 'acoes' },
        h('button', { class: 'btn', disabled: !!a?.reconhecido, onclick: () => void agir('ack', o.alerta_id) }, 'Reconhecer'),
        h('button', { class: 'btn', disabled: !!a?.silenciado, onclick: () => void agir('mute', o.alerta_id) }, 'Silenciar'),
        h('button', {
          class: 'btn perigo',
          disabled: !podeDesligar(u.papel),
          title: podeDesligar(u.papel) ? '' : `O papel "${u.papel}" não pode desligar o alarme.`,
          onclick: () => { desligando = !desligando; renderInfo(); },
        }, 'Desligar alarme…'),
      ),
      desligando && formDesligar(o.alerta_id),
    ]);
  }

  function formDesligar(id: string) {
    const motivo = h('textarea', { rows: 2, placeholder: 'Motivo (fica no histórico de auditoria)' });
    return h('div', { class: 'form-desligar' }, motivo,
      h('button', { class: 'btn perigo', onclick: () => void agir('off', id, motivo.value) }, 'Confirmar desligamento'));
  }

  async function agir(tipo: 'ack' | 'mute' | 'off', id: string, motivo?: string) {
    const u = sessao();
    try {
      if (tipo === 'ack') await api.reconhecer(id, u.usuario);
      else if (tipo === 'mute') await api.silenciar(id, u.usuario);
      else await api.desligar(id, u.usuario, u.papel, motivo);
      toast({ ack: 'Alerta reconhecido.', mute: 'Alerta silenciado.', off: 'Desligamento registrado.' }[tipo]);
      desligando = false;
      await carregar();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : String(e), 'erro');
    }
  }

  void carregar();
  const timer = setInterval(() => void carregar(), POLL_MS);
  return () => clearInterval(timer);
}

function badge(sev: Severidade) {
  return h('span', { class: `badge sev-${sev}` }, sev);
}
