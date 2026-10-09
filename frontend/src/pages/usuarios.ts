import { api } from '../api';
import { sessao } from '../session';
import type { Papel, Usuario } from '../types';
import { h, limpar, toast } from '../ui';

const PAPEIS: Papel[] = ['operador', 'supervisor', 'auditor', 'administrador'];
const DESCRICAO: Record<Papel, string> = {
  operador: 'acompanha e reconhece alertas',
  supervisor: 'também desliga alarmes e configura zonas e políticas',
  auditor: 'consulta histórico e relatórios',
  administrador: 'tudo, incluindo EPIs e usuários',
};

export function paginaUsuarios(root: HTMLElement): () => void {
  let usuarios: Usuario[] = [];
  const tabela = h('div', null);

  const id = h('input', { type: 'text', placeholder: 'ex.: joana.silva', autocomplete: 'off' });
  const nome = h('input', { type: 'text', placeholder: 'ex.: Joana Silva' });
  const papel = h('select', null, ...PAPEIS.map((p) => h('option', { value: p }, p)));
  const senha = h('input', { type: 'password', autocomplete: 'new-password', placeholder: 'mínimo 4 caracteres' });

  root.append(
    h('header', { class: 'pagina-topo' },
      h('div', null, h('h1', null, 'Usuários'),
        h('p', { class: 'sub' }, 'Quem acessa o A5 e com qual papel. O backend decide as permissões a partir do papel da sessão.'))),
    h('section', { class: 'painel' },
      h('h2', null, 'Novo usuário'),
      h('div', { class: 'grade-campos' },
        h('label', { class: 'campo' }, 'Login', id), h('label', { class: 'campo' }, 'Nome', nome),
        h('label', { class: 'campo' }, 'Papel', papel), h('label', { class: 'campo' }, 'Senha inicial', senha)),
      h('p', { class: 'meta' }, ...PAPEIS.map((p) => h('span', null, h('strong', null, p), ` — ${DESCRICAO[p]}. `))),
      h('div', { class: 'acoes' }, h('button', { class: 'btn primario', onclick: () => void criar() }, 'Cadastrar'))),
    h('section', { class: 'painel' }, tabela),
  );

  async function carregar() {
    try {
      usuarios = await api.usuarios();
      render();
    } catch (e) {
      limpar(tabela);
      tabela.append(h('p', { class: 'erro' }, e instanceof Error ? e.message : String(e)));
    }
  }

  function render() {
    limpar(tabela);
    tabela.append(h('table', { class: 'tabela' },
      h('thead', null, h('tr', null, ...['Login', 'Nome', 'Papel', 'Situação', ''].map((t) => h('th', null, t)))),
      h('tbody', null, ...usuarios.map(linha))));
  }

  function linha(u: Usuario) {
    const eu = u.id === sessao().usuario;
    const sel = h('select', { disabled: eu, title: eu ? 'Você não altera o próprio papel.' : '' },
      ...PAPEIS.map((p) => h('option', { value: p, selected: p === u.papel }, p)));
    sel.addEventListener('change', () => void atualizar(u.id, { papel: sel.value as Papel }, 'Papel atualizado.'));
    return h('tr', { class: u.ativo ? '' : 'inativo' },
      h('td', { class: 'mono' }, u.id, eu && h('span', { class: 'chip' }, 'você')),
      h('td', null, u.nome),
      h('td', null, sel),
      h('td', null, h('span', { class: `chip${u.ativo ? ' ok' : ''}` }, u.ativo ? 'ativo' : 'inativo')),
      h('td', null, h('div', { class: 'acoes' },
        h('button', { class: 'btn pequeno', onclick: () => void redefinir(u) }, 'Nova senha'),
        !eu && h('button', {
          class: `btn pequeno${u.ativo ? ' perigo' : ''}`,
          onclick: () => void atualizar(u.id, { ativo: !u.ativo }, u.ativo ? 'Usuário desativado.' : 'Usuário reativado.'),
        }, u.ativo ? 'Desativar' : 'Reativar'))));
  }

  async function atualizar(uid: string, dados: Parameters<typeof api.atualizarUsuario>[1], ok: string) {
    try {
      await api.atualizarUsuario(uid, dados);
      toast(ok);
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'erro');
    }
    await carregar();
  }

  async function redefinir(u: Usuario) {
    const nova = window.prompt(`Nova senha para ${u.id} (mínimo 4 caracteres):`);
    if (nova) await atualizar(u.id, { senha: nova }, 'Senha redefinida.');
  }

  async function criar() {
    try {
      await api.criarUsuario({ id: id.value.trim(), nome: nome.value.trim() || id.value.trim(), papel: papel.value as Papel, senha: senha.value || undefined });
      toast('Usuário cadastrado.');
      id.value = nome.value = senha.value = '';
      await carregar();
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e), 'erro');
    }
  }

  void carregar();
  return () => {};
}
