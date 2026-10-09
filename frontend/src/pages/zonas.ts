import { ZoneEditor } from '../../vendor/b6/b6-zone-editor/b6_zone_editor';
import { ignorarCliqueNaoPrimario, pontosSvg, poligonoUnico } from '../adapters/b6';
import { api } from '../api';
import { podeConfigurar, sessao } from '../session';
import type { Politica, Ponto, Turno, ZonaCadastro } from '../types';
import { append, dataHora, h, limpar, toast } from '../ui';

const SLUG = /^[A-Za-z0-9_.-]+$/;
const texto = (v: string): string | null => v.trim() || null;

export function paginaZonas(root: HTMLElement): () => void {
  const editavel = podeConfigurar(sessao().papel);
  let zonas: ZonaCadastro[] = [];
  let politicas: Politica[] = [];
  let aberta: string | null = null; // null = nova zona
  let mostrarInativas = false;
  let seqAbrir = 0;

  const lista = h('div', { class: 'lista' });
  const detalhe = h('section', { class: 'painel editor-politica' });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'Zonas'),
        h('p', { class: 'sub' }, 'Onde o monitoramento vale: identificação, câmera, polígono no quadro e turnos. A política de EPI de cada zona fica em Políticas.'))),
    h('div', { class: 'duas-colunas' },
      h('aside', { class: 'painel coluna-lista' },
        editavel && h('button', { class: 'btn primario cheio', onclick: () => void abrir(null) }, '+ Nova zona'),
        h('label', { class: 'campo inline' },
          h('input', { type: 'checkbox', onchange: (e: Event) => { mostrarInativas = (e.target as HTMLInputElement).checked; void carregar(aberta); } }),
          'Mostrar zonas desativadas'),
        lista),
      detalhe),
  );

  async function carregar(abrirId?: string | null) {
    try {
      [zonas, politicas] = await Promise.all([api.zonas(mostrarInativas), api.politicasVigentes()]);
      renderLista();
      await abrir(abrirId !== undefined ? abrirId : (zonas[0]?.id ?? null));
    } catch (e) {
      lista.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function renderLista() {
    limpar(lista);
    if (zonas.length === 0) lista.append(h('p', { class: 'vazio' }, 'Nenhuma zona cadastrada.'));
    for (const z of zonas) {
      const pol = politicas.find((p) => p.zona.id === z.id);
      lista.append(
        h('button', { class: `card-ocorrencia${z.id === aberta ? ' ativo' : ''}`, onclick: () => void abrir(z.id) },
          h('strong', null, z.nome || z.id),
          h('div', { class: 'meta mono' }, z.id),
          h('div', { class: 'chips' },
            h('span', { class: `chip${pol ? ' ok' : ''}` }, pol ? `política v${pol.versao}` : 'sem política'),
            !z.ativa && h('span', { class: 'chip mudo' }, 'desativada'),
            z.poligono.length >= 3 && h('span', { class: 'chip' }, 'polígono'),
            z.camera_id && h('span', { class: 'chip' }, z.camera_id))));
    }
  }

  async function abrir(id: string | null) {
    const minha = ++seqAbrir;
    aberta = id;
    renderLista();
    let turnos: Turno[] = [];
    let ativo: boolean | null = null;
    if (id) {
      try {
        [turnos, ativo] = await Promise.all([api.turnos(id), api.monitoramentoAtivo(id).then((r) => r.ativo)]);
      } catch (e) { toast(e instanceof Error ? e.message : String(e), 'erro'); }
    }
    if (minha !== seqAbrir) return;
    montar(zonas.find((z) => z.id === id) ?? null, turnos, ativo);
  }

  function montar(zona: ZonaCadastro | null, turnosIniciais: Turno[], ativoAgora: boolean | null) {
    limpar(detalhe);
    const pol = zona ? politicas.find((p) => p.zona.id === zona.id) : undefined;

    const campoId = h('input', { type: 'text', value: zona?.id ?? '', placeholder: 'ex.: zona-producao-1', disabled: !!zona });
    const campoNome = h('input', { type: 'text', value: zona?.nome ?? '', placeholder: 'ex.: Produção 1', disabled: !editavel });
    const campoDesc = h('input', { type: 'text', value: zona?.descricao ?? '', placeholder: 'ex.: Linha de montagem, bloco A', disabled: !editavel });
    const campoCamera = h('input', { type: 'text', value: zona?.camera_id ?? '', placeholder: 'ex.: cam-01 (S1)', disabled: !editavel });

    // --- polígono (B6 ZoneEditor) ---
    const salvo: Ponto[] = zona?.poligono ?? [];
    let remover = false;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('class', 'zona-atual');
    if (salvo.length >= 3) {
      const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      poly.setAttribute('points', pontosSvg(salvo));
      svg.appendChild(poly);
    }
    const hostZona = h('div', { id: 'zone-host', class: 'zone-host' }, svg);
    const arquivoFundo = h('input', {
      type: 'file', accept: 'image/*', class: 'oculto',
      onchange: () => {
        const f = arquivoFundo.files?.[0];
        if (f) hostZona.style.backgroundImage = `url(${URL.createObjectURL(f)})`;
      },
    });
    let editor: ZoneEditor | null = null;
    const avisoRemover = h('p', { class: 'aviso', hidden: true }, 'O polígono salvo será removido ao salvar.');

    // --- turnos ---
    let turnos: Turno[] = turnosIniciais.map((t) => ({ inicio: t.inicio, fim: t.fim }));
    const caixaTurnos = h('div', { class: 'turnos' });
    function renderTurnos() {
      limpar(caixaTurnos);
      if (turnos.length === 0) caixaTurnos.append(h('p', { class: 'meta' }, 'Sem turnos: o monitoramento fica sempre ativo.'));
      turnos.forEach((t, i) => {
        const ini = h('input', { type: 'time', value: t.inicio, disabled: !editavel, onchange: () => { t.inicio = ini.value; } });
        const fim = h('input', { type: 'time', value: t.fim, disabled: !editavel, onchange: () => { t.fim = fim.value; } });
        caixaTurnos.append(h('div', { class: 'turno' },
          h('label', { class: 'campo mini' }, 'início', ini), h('label', { class: 'campo mini' }, 'fim', fim),
          fim.value && ini.value && fim.value < ini.value && h('span', { class: 'chip' }, 'vira a noite'),
          editavel && h('button', { class: 'btn pequeno', onclick: () => { turnos.splice(i, 1); renderTurnos(); } }, 'Remover')));
      });
    }
    renderTurnos();

    append(detalhe, [
      h('div', { class: 'linha' },
        h('h2', null, zona ? (zona.nome || zona.id) : 'Nova zona'),
        zona && h('span', { class: 'meta' }, `atualizada em ${dataHora(zona.atualizada_em)}`)),
      h('div', { class: 'grade-campos' },
        h('label', { class: 'campo' }, 'ID da zona', campoId),
        h('label', { class: 'campo' }, 'Nome', campoNome),
        h('label', { class: 'campo' }, 'Descrição', campoDesc),
        h('label', { class: 'campo' }, 'Câmera', campoCamera)),
      zona && !zona.ativa && h('p', { class: 'aviso' }, 'Zona desativada: não aparece nas outras telas nem aceita novas políticas.'),
      zona && h('p', { class: 'meta' }, 'Política: ',
        pol ? `${pol.id} · v${pol.versao} · ${pol.equipamentos_obrigatorios.map((e) => e.epi_id).join(', ')} ` : 'esta zona ainda não tem política. ',
        h('a', { href: '#/politicas' }, pol ? 'Ver' : 'Definir')),

      h('h3', null, 'Zona monitorada (polígono)'),
      h('p', { class: 'meta' },
        'Clique para marcar os pontos e use o botão direito para fechar o polígono. ',
        salvo.length >= 3 ? 'O polígono salvo aparece tracejado; desenhar outro o substitui ao salvar.' : 'Sem polígono: vale para o quadro inteiro.',
        pol && editavel ? ' Mudar o polígono gera automaticamente uma nova versão da política.' : ''),
      hostZona,
      avisoRemover,
      editavel && h('div', { class: 'acoes' },
        h('button', { class: 'btn', onclick: () => editor?.startDrawingMode() }, 'Iniciar desenho'),
        h('button', { class: 'btn', onclick: () => editor?.stopDrawingMode() }, 'Parar'),
        h('button', { class: 'btn', onclick: () => editor?.clearAll() }, 'Limpar desenho'),
        salvo.length >= 3 && h('button', {
          class: 'btn perigo',
          onclick: () => { remover = true; svg.style.display = 'none'; avisoRemover.hidden = false; },
        }, 'Remover polígono salvo'),
        h('button', { class: 'btn', onclick: () => arquivoFundo.click() }, 'Imagem de fundo…'), arquivoFundo),

      editavel && h('div', { class: 'acoes fim' },
        zona && zona.ativa && h('button', { class: 'btn perigo', onclick: () => void desativar(zona) }, 'Desativar zona'),
        zona && !zona.ativa && h('button', { class: 'btn', onclick: () => void reativar(zona) }, 'Reativar zona'),
        zona && h('button', { class: 'btn perigo', onclick: () => void apagar(zona) }, 'Apagar zona'),
        h('button', { class: 'btn primario', onclick: () => void salvar(zona) }, zona ? 'Salvar zona' : 'Criar zona')),

      zona && h('div', null,
        h('div', { class: 'linha' }, h('h3', null, 'Turnos de monitoramento'),
          ativoAgora !== null && h('span', { class: `chip${ativoAgora ? ' ok' : ''}` }, ativoAgora ? 'ativo agora' : 'fora de turno')),
        caixaTurnos,
        editavel && h('div', { class: 'acoes' },
          h('button', { class: 'btn', onclick: () => { turnos.push({ inicio: '08:00', fim: '17:00' }); renderTurnos(); } }, '+ Turno'),
          h('button', { class: 'btn primario', onclick: () => void salvarTurnos(zona) }, 'Salvar turnos'))),
    ]);

    ignorarCliqueNaoPrimario(hostZona);
    editor = new ZoneEditor('zone-host');

    async function salvar(atual: ZonaCadastro | null) {
      const id = (atual?.id ?? campoId.value).trim();
      if (!SLUG.test(id)) return toast('ID da zona: use letras, números, ".", "-" ou "_".', 'erro');
      let desenhado: Ponto[] | null;
      try {
        desenhado = poligonoUnico(editor!.exportAllZones(campoNome.value || id, 'ZONE'));
      } catch (e) {
        return toast(e instanceof Error ? e.message : String(e), 'erro');
      }
      try {
        const dados = { nome: texto(campoNome.value), descricao: texto(campoDesc.value), camera_id: texto(campoCamera.value) };
        if (!atual) {
          await api.criarZona({ id, ...dados, poligono: desenhado ?? [] });
          toast(`Zona ${id} criada.`);
        } else {
          const antes = politicas.find((p) => p.zona.id === id)?.versao;
          await api.atualizarZona(id, { ...dados, ...(desenhado ? { poligono: desenhado } : remover ? { poligono: [] } : {}) });
          const depois = (await api.politicasVigentes()).find((p) => p.zona.id === id)?.versao;
          toast(depois && depois !== antes ? `Zona salva; política atualizada para v${depois}.` : 'Zona salva.');
        }
        await carregar(id);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }

    async function desativar(z: ZonaCadastro) {
      if (!window.confirm(`Desativar a zona "${z.nome || z.id}"? Ela some da lista e não aceita novas políticas; o histórico continua.`)) return;
      try {
        await api.desativarZona(z.id);
        toast('Zona desativada.');
        await carregar(null);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }

    async function reativar(z: ZonaCadastro) {
      try {
        await api.atualizarZona(z.id, { ativa: true });
        toast('Zona reativada.');
        await carregar(z.id);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }

    async function apagar(z: ZonaCadastro) {
      if (!window.confirm(`Apagar a zona "${z.nome || z.id}" de vez? Só é possível se ela nunca teve política nem ação no histórico; senão, use Desativar.`)) return;
      try {
        await api.apagarZona(z.id);
        toast('Zona apagada.');
        await carregar(null);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }

    async function salvarTurnos(z: ZonaCadastro) {
      if (turnos.some((t) => !t.inicio || !t.fim || t.inicio === t.fim)) {
        return toast('Cada turno precisa de início e fim diferentes.', 'erro');
      }
      try {
        await api.salvarTurnos(z.id, turnos);
        toast('Turnos salvos.');
        await abrir(z.id);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }
  }

  void carregar();
  return () => {};
}
