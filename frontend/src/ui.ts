type Child = Node | string | number | null | undefined | false;
type Props = Record<string, unknown> | null;

/** Criador de elementos minimalista: h('button', { class: 'btn', onclick: fn }, 'texto'). */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: Props = null,
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props ?? {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'class') el.className = String(value);
    else if (key.startsWith('on') && typeof value === 'function') {
      el.addEventListener(key.slice(2), value as EventListener);
    } else if (key in el && key !== 'list') (el as unknown as Record<string, unknown>)[key] = value;
    else el.setAttribute(key, value === true ? '' : String(value));
  }
  append(el, children);
  return el;
}

export function append(parent: Node, children: Child[]): void {
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    parent.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

export function limpar(el: Element): void {
  while (el.firstChild) el.removeChild(el.firstChild);
}

export function toast(mensagem: string, tipo: 'ok' | 'erro' = 'ok'): void {
  let area = document.getElementById('toasts');
  if (!area) {
    area = h('div', { id: 'toasts', 'aria-live': 'polite' });
    document.body.appendChild(area);
  }
  const t = h('div', { class: `toast ${tipo}` }, mensagem);
  area.appendChild(t);
  setTimeout(() => t.remove(), tipo === 'erro' ? 6000 : 3000);
}

export function dataHora(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('pt-BR');
}

export const pct = (v: number) => `${Math.round(v * 100)}%`;

/** Datas de <input type="date"> ('AAAA-MM-DD', dia local) -> ISO-8601 em UTC para a API. */
export const inicioDoDia = (d: string): string | undefined => (d ? new Date(`${d}T00:00:00`).toISOString() : undefined);
export const fimDoDia = (d: string): string | undefined => (d ? new Date(`${d}T23:59:59.999`).toISOString() : undefined);

/** "face shield,  viseira, FACE SHIELD" -> ['face shield', 'viseira'] (sem vazios; o backend remove repetidos por caixa). */
export function listaDeAliases(texto: string): string[] {
  return texto.split(',').map((a) => a.trim().replace(/\s+/g, ' ')).filter(Boolean);
}
