import { api } from '../api';
import { ehAdministrador, sessao } from '../session';
import type { EPI } from '../types';
import { h, limpar, listaDeAliases, toast } from '../ui';

export function paginaEpis(root: HTMLElement): () => void {
  const admin = ehAdministrador(sessao().papel);
  let epis: EPI[] = [];
  const tabela = h('div', null);

  const novoId = h('input', { type: 'text', placeholder: 'ex.: protetor_facial' });
  const novoNome = h('input', { type: 'text', placeholder: 'ex.: Protetor facial' });
  const novosAliases = h('input', { type: 'text', placeholder: 'ex.: face shield, viseira' });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'EPIs'),
        h('p', { class: 'sub' }, 'Catálogo global. Os aliases são os nomes de classe que o detector (I9) pode emitir; vale sem diferenciar maiúsculas e acentos.'))),
    ...(admin ? [h('section', { class: 'painel' },
      h('h2', null, 'Novo EPI'),
      h('div', { class: 'grade-campos' },
        h('label', { class: 'campo' }, 'ID (minúsculas, números e _)', novoId),
        h('label', { class: 'campo' }, 'Nome', novoNome),
        h('label', { class: 'campo' }, 'Aliases (separe por vírgula)', novosAliases)),
      h('div', { class: 'acoes' }, h('button', { class: 'btn primario', onclick: () => void criar() }, 'Adicionar EPI')))] : []),
    h('section', { class: 'painel' }, tabela),
  );

  async function carregar() {
    try {
      epis = await api.epis();
      render();
    } catch (e) {
      limpar(tabela);
      tabela.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function render() {
    limpar(tabela);
    tabela.append(h('table', { class: 'tabela' },
      h('thead', null, h('tr', null, ...['ID', 'Nome', 'Aliases', 'Situação', ''].map((t) => h('th', null, t)))),
      h('tbody', null, ...epis.map(linha))));
  }

  function linha(e: EPI) {
    const nome = h('input', { type: 'text', value: e.nome, disabled: !admin });
    const aliases = h('input', { type: 'text', value: e.aliases.join(', '), disabled: !admin });
    return h('tr', { class: e.ativo ? '' : 'inativo' },
      h('td', { class: 'mono' }, e.id),
      h('td', null, nome),
      h('td', null, aliases),
      h('td', null, h('span', { class: `chip${e.ativo ? ' ok' : ''}` }, e.ativo ? 'ativo' : 'inativo')),
      h('td', null, admin && h('div', { class: 'acoes' },
        h('button', {
          class: 'btn pequeno',
          onclick: () => void salvar(e.id, { nome: nome.value.trim(), aliases: listaDeAliases(aliases.value) }, 'EPI salvo.'),
        }, 'Salvar'),
        h('button', {
          class: `btn pequeno${e.ativo ? ' perigo' : ''}`,
          onclick: () => void salvar(e.id, { ativo: !e.ativo }, e.ativo ? 'EPI desativado.' : 'EPI reativado.'),
        }, e.ativo ? 'Desativar' : 'Reativar'),
      )));
  }

  async function salvar(id: string, dados: Parameters<typeof api.atualizarEpi>[1], ok: string) {
    try {
      await api.atualizarEpi(id, dados);
      toast(ok);
      await carregar();
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'erro');
    }
  }

  async function criar() {
    try {
      await api.criarEpi({ id: novoId.value.trim(), nome: novoNome.value.trim(), aliases: listaDeAliases(novosAliases.value) });
      toast('EPI adicionado.');
      novoId.value = novoNome.value = novosAliases.value = '';
      await carregar();
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'erro');
    }
  }

  void carregar();
  return () => {};
}
