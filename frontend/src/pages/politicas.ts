import { pontosSvg } from '../adapters/b6';
import { api } from '../api';
import { podeConfigurar, sessao } from '../session';
import type { EPI, EquipamentoExigido, NovaPolitica, Politica, ZonaCadastro } from '../types';
import { append, dataHora, h, limpar, toast } from '../ui';

const num = (v: string): number | null => (v.trim() === '' ? null : Number(v));

export function paginaPoliticas(root: HTMLElement): () => void {
  const editavel = podeConfigurar(sessao().papel);
  let epis: EPI[] = [];
  let zonas: ZonaCadastro[] = [];
  let vigentes: Politica[] = [];
  let zonaAberta: string | null = null;
  let seqAbrir = 0; // cliques rápidos entre zonas: só o último monta o formulário

  const lista = h('div', { class: 'lista' });
  const editorPane = h('section', { class: 'painel editor-politica' });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'Políticas'),
        h('p', { class: 'sub' }, 'Uma política por zona, com todos os EPIs obrigatórios dela. Salvar cria uma nova versão; só a última vale.'))),
    h('div', { class: 'duas-colunas' }, h('aside', { class: 'painel coluna-lista' }, lista), editorPane),
  );

  async function carregar(abrirId?: string) {
    try {
      [epis, zonas, vigentes] = await Promise.all([api.epis(), api.zonas(), api.politicasVigentes()]);
      renderLista();
      await abrir(abrirId ?? zonaAberta ?? zonas[0]?.id ?? null);
    } catch (e) {
      lista.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function renderLista() {
    limpar(lista);
    if (zonas.length === 0) {
      lista.append(h('p', { class: 'vazio' }, 'Nenhuma zona cadastrada. ', h('a', { href: '#/zonas' }, 'Cadastre uma zona'), ' para definir a política.'));
    }
    for (const z of zonas) {
      const p = vigentes.find((x) => x.zona.id === z.id);
      lista.append(
        h('button', { class: `card-ocorrencia${z.id === zonaAberta ? ' ativo' : ''}`, onclick: () => void abrir(z.id) },
          h('div', { class: 'linha' }, h('strong', null, z.nome || z.id),
            h('span', { class: `chip${p ? ' ok' : ''}` }, p ? `v${p.versao}` : 'sem política')),
          h('div', { class: 'meta mono' }, z.id),
          p && h('div', { class: 'chips' }, ...p.equipamentos_obrigatorios.map((e) => h('span', { class: 'chip' }, e.epi_id)))));
    }
  }

  /** Abre a zona; `base` carrega uma versão antiga como ponto de partida. */
  async function abrir(zonaId: string | null, base?: Politica) {
    const minha = ++seqAbrir;
    zonaAberta = zonaId;
    renderLista();
    if (!zonaId) {
      limpar(editorPane);
      editorPane.append(h('p', { class: 'vazio centro' }, 'Selecione uma zona.'));
      return;
    }
    let versoes: Politica[] = [];
    try { versoes = (await api.versoes(zonaId)).slice().reverse(); } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'erro');
    }
    if (minha !== seqAbrir) return;
    montarEditor(zonas.find((z) => z.id === zonaId)!, base ?? versoes[0] ?? null, versoes);
  }

  function montarEditor(zona: ZonaCadastro, base: Politica | null, versoes: Politica[]) {
    limpar(editorPane);
    const vigente = versoes[0];

    const campoPolitica = h('input', { type: 'text', value: base?.id ?? '', placeholder: `padrão: politica-${zona.id}`, disabled: !!vigente || !editavel });
    const campoClasse = h('input', { type: 'text', value: base?.classe_pessoa ?? 'pessoa', disabled: !editavel });
    const campoTempo = h('input', { type: 'number', min: 0, step: 1, value: String(base?.tempo_tolerancia_segundos ?? 10), disabled: !editavel });
    const campoConf = h('input', { type: 'number', min: 0, max: 1, step: 0.05, value: String(base?.confianca_minima ?? 0.6), disabled: !editavel });

    const linhas = epis.filter((e) => e.ativo).map((epi) => {
      const atual = base?.equipamentos_obrigatorios.find((e) => e.epi_id === epi.id);
      const marcado = h('input', { type: 'checkbox', checked: !!atual, disabled: !editavel });
      const tempo = h('input', { type: 'number', min: 0, step: 1, value: atual?.tempo_tolerancia_segundos?.toString() ?? '', disabled: !atual || !editavel });
      const conf = h('input', { type: 'number', min: 0, max: 1, step: 0.05, value: atual?.confianca_minima?.toString() ?? '', disabled: !atual || !editavel });
      marcado.addEventListener('change', () => { tempo.disabled = conf.disabled = !marcado.checked; });
      const placeholders = () => { tempo.placeholder = `padrão ${campoTempo.value}s`; conf.placeholder = `padrão ${campoConf.value}`; };
      campoTempo.addEventListener('input', placeholders);
      campoConf.addEventListener('input', placeholders);
      placeholders();
      const row = h('div', { class: `equip${atual ? ' marcado' : ''}` },
        h('label', { class: 'equip-nome' }, marcado, h('span', null, epi.nome),
          h('span', { class: 'aliases mono' }, epi.aliases.join(' · '))),
        h('label', { class: 'campo mini' }, 'tolerância (s)', tempo),
        h('label', { class: 'campo mini' }, 'confiança mín.', conf));
      marcado.addEventListener('change', () => row.classList.toggle('marcado', marcado.checked));
      return { epi, marcado, tempo, conf, row };
    });

    // Prévia somente leitura da zona (quem edita o polígono é a tela de Zonas).
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('class', 'zona-atual');
    if (zona.poligono.length >= 3) {
      const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
      poly.setAttribute('points', pontosSvg(zona.poligono));
      svg.appendChild(poly);
    }

    const titulo = vigente
      ? `Editando a partir da v${base?.versao}${base && base.versao !== vigente.versao ? ' (antiga)' : ''} · a próxima será v${vigente.versao + 1}`
      : 'Sem política · será a v1';

    append(editorPane, [
      h('div', { class: 'linha' }, h('h2', null, zona.nome || zona.id), h('span', { class: 'meta' }, titulo)),
      h('div', { class: 'zona-previa' },
        h('div', { class: 'zone-host mini' }, svg),
        h('div', null,
          h('p', { class: 'meta mono' }, zona.id),
          h('p', { class: 'meta' }, zona.poligono.length >= 3 ? `Polígono com ${zona.poligono.length} pontos.` : 'Sem polígono: vale para o quadro inteiro.'),
          h('p', { class: 'meta' }, zona.camera_id ? `Câmera ${zona.camera_id}.` : 'Sem câmera vinculada.'),
          h('a', { href: '#/zonas' }, 'Editar a zona'))),

      h('div', { class: 'grade-campos' },
        h('label', { class: 'campo' }, 'ID da política', campoPolitica),
        h('label', { class: 'campo' }, 'Classe de pessoa', campoClasse)),

      h('h3', null, 'Equipamentos obrigatórios'),
      h('div', { class: 'grade-campos padrao' },
        h('label', { class: 'campo' }, 'Tolerância padrão (s)', campoTempo),
        h('label', { class: 'campo' }, 'Confiança mínima padrão', campoConf)),
      h('p', { class: 'meta' }, 'Deixe tolerância/confiança do equipamento em branco para herdar o padrão. ',
        'Faltando algum EPI? ', h('a', { href: '#/epis' }, 'Catálogo de EPIs')),
      h('div', { class: 'equips' }, ...linhas.map((l) => l.row)),

      editavel
        ? h('div', { class: 'acoes fim' },
            h('button', { class: 'btn primario', onclick: () => void salvar() }, vigente ? `Salvar como v${vigente.versao + 1}` : 'Salvar política'))
        : h('p', { class: 'aviso' }, `O papel "${sessao().papel}" só consulta políticas.`),

      versoes.length > 0 && h('div', null,
        h('h3', null, 'Versões'),
        h('table', { class: 'tabela' }, h('tbody', null, ...versoes.map((v, i) =>
          h('tr', null,
            h('td', null, h('span', { class: 'chip' }, `v${v.versao}`), i === 0 && h('span', { class: 'chip ok' }, 'vigente')),
            h('td', { class: 'meta' }, dataHora(v.criada_em)),
            h('td', null, v.equipamentos_obrigatorios.map((e) => e.epi_id).join(', ')),
            h('td', null, editavel && h('button', { class: 'btn pequeno', onclick: () => void abrir(zona.id, v) }, 'Usar como base'))))))),
    ]);

    async function salvar() {
      const equipamentos: EquipamentoExigido[] = linhas
        .filter((l) => l.marcado.checked)
        .map((l) => ({ epi_id: l.epi.id, tempo_tolerancia_segundos: num(l.tempo.value), confianca_minima: num(l.conf.value) }));
      if (equipamentos.length === 0) return toast('Marque pelo menos um equipamento obrigatório.', 'erro');
      // A zona vem do cadastro: só o id vai junto (geometria e nome o backend herda).
      const corpo: NovaPolitica = {
        id: campoPolitica.value.trim() || null,
        zona: { id: zona.id },
        classe_pessoa: campoClasse.value.trim() || 'pessoa',
        equipamentos_obrigatorios: equipamentos,
        tempo_tolerancia_segundos: Number(campoTempo.value),
        confianca_minima: Number(campoConf.value),
      };
      try {
        const salva = await api.definirPolitica(zona.id, corpo);
        toast(`Política ${salva.id} salva como v${salva.versao}.`);
        await carregar(zona.id);
      } catch (e) {
        toast(e instanceof Error ? e.message : String(e), 'erro');
      }
    }
  }

  void carregar();
  return () => {};
}
