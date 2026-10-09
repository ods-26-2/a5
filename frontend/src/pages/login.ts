import { api } from '../api';
import { iniciarSessao } from '../session';
import { h } from '../ui';

/** Tela de entrada. `aoEntrar` roda depois que a sessão foi guardada. */
export function paginaLogin(root: HTMLElement, aoEntrar: () => void, aviso?: string): void {
  const id = h('input', { type: 'text', autocomplete: 'username', required: true, autofocus: true });
  const senha = h('input', { type: 'password', autocomplete: 'current-password', required: true });
  const erro = h('p', { class: 'erro', role: 'alert' }, aviso ?? '');
  const botao = h('button', { class: 'btn primario cheio', type: 'submit' }, 'Entrar');

  const form = h('form', {
    class: 'painel login',
    onsubmit: async (ev: Event) => {
      ev.preventDefault();
      botao.disabled = true;
      erro.textContent = '';
      try {
        const r = await api.login(id.value.trim(), senha.value);
        iniciarSessao(r.token, r.usuario);
        aoEntrar();
      } catch (e) {
        erro.textContent = e instanceof Error ? e.message : String(e);
        botao.disabled = false;
      }
    },
  },
    h('div', { class: 'marca' }, h('span', { class: 'logo' }, 'A5'), h('span', null, 'EPI · Segurança')),
    h('label', { class: 'campo' }, 'Usuário', id),
    h('label', { class: 'campo' }, 'Senha', senha),
    erro,
    botao,
    import.meta.env.DEV && h('p', { class: 'meta' },
      'Desenvolvimento: operador, supervisor, auditor (senha ', h('span', { class: 'mono' }, '<papel>123'),
      ') e administrador (senha ', h('span', { class: 'mono' }, 'admin123'), ').'));

  root.append(h('div', { class: 'login-pagina' }, form));
}
