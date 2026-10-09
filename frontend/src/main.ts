import './styles.css';
import { api, definirAoExpirar } from './api';
import { paginaEpis } from './pages/epis';
import { paginaHistorico } from './pages/historico';
import { paginaLogin } from './pages/login';
import { paginaPoliticas } from './pages/politicas';
import { paginaSupervisao } from './pages/supervisao';
import { paginaUsuarios } from './pages/usuarios';
import { paginaZonas } from './pages/zonas';
import { ROTAS, rotaPermitida } from './routes';
import { encerrarSessao, iniciarSessao, sessao, temSessao } from './session';
import { h, limpar } from './ui';

const PAGINAS: Record<string, (el: HTMLElement) => () => void> = {
  '/supervisao': paginaSupervisao,
  '/zonas': paginaZonas,
  '/politicas': paginaPoliticas,
  '/epis': paginaEpis,
  '/historico': paginaHistorico,
  '/usuarios': paginaUsuarios,
};

const app = document.getElementById('app')!;
let dispose: (() => void) | null = null;
let timerSaude: ReturnType<typeof setInterval> | null = null;

function mostrarLogin(aviso?: string) {
  dispose?.();
  dispose = null;
  if (timerSaude) clearInterval(timerSaude);
  limpar(app);
  paginaLogin(app, mostrarApp, aviso);
}

function mostrarApp() {
  limpar(app);
  const u = sessao();
  const conteudo = h('main', { class: 'conteudo' });
  const nav = h('nav', { class: 'nav' });
  const saude = h('span', { class: 'saude', title: 'Verificando…' }, h('i'), 'backend');

  const sair = async () => {
    try { await api.logout(); } catch { /* sessão pode já ter expirado */ }
    encerrarSessao();
    mostrarLogin();
  };

  app.append(
    h('header', { class: 'topo' },
      h('div', { class: 'marca' }, h('span', { class: 'logo' }, 'A5'), h('span', null, 'EPI · Segurança')),
      nav,
      h('div', { class: 'sessao' }, saude,
        h('span', { class: 'quem' }, u.nome || u.usuario, h('span', { class: 'chip' }, u.papel)),
        h('button', { class: 'btn pequeno', onclick: () => void sair() }, 'Sair'))),
    conteudo);

  function navegar() {
    const pedida = location.hash.replace(/^#/, '') || '/supervisao';
    const rota = rotaPermitida(pedida, u.papel);
    dispose?.();
    limpar(conteudo);
    limpar(nav);
    for (const [path, r] of Object.entries(ROTAS)) {
      if (!r.visivel(u.papel)) continue;
      nav.append(h('a', { href: `#${path}`, class: path === rota ? 'ativo' : '' }, r.titulo));
    }
    document.title = `${ROTAS[rota].titulo} · A5 EPI`;
    dispose = PAGINAS[rota](conteudo);
  }

  async function verificarSaude() {
    try {
      const s = await api.saude();
      const ruim = Object.entries(s).filter(([, v]) => !v.startsWith('ok'));
      saude.className = `saude ${ruim.length ? 'ruim' : 'ok'}`;
      saude.title = Object.entries(s).map(([k, v]) => `${k}: ${v}`).join('\n');
    } catch {
      saude.className = 'saude ruim';
      saude.title = 'Backend A5 inacessível';
    }
  }

  window.onhashchange = navegar;
  navegar();
  void verificarSaude();
  timerSaude = setInterval(() => void verificarSaude(), 30_000);
}

async function iniciar() {
  definirAoExpirar(() => mostrarLogin('Sua sessão expirou. Entre novamente.'));
  if (!temSessao()) return mostrarLogin();
  try {
    // Confere o token guardado; também atualiza nome/papel se mudaram no backend.
    const eu = await api.eu();
    iniciarSessao(sessao().token, eu);
    mostrarApp();
  } catch {
    // 401 já cai em mostrarLogin via aoExpirar; backend fora do ar vem para cá.
    if (temSessao()) mostrarApp();
  }
}

void iniciar();
