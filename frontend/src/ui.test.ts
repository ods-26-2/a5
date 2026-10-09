import { describe, expect, it } from 'vitest';
import { fimDoDia, inicioDoDia, listaDeAliases } from './ui';

describe('inicioDoDia / fimDoDia', () => {
  it('cobrem o dia local inteiro e convertem para ISO UTC', () => {
    expect(new Date(inicioDoDia('2026-09-23')!).getTime()).toBe(new Date(2026, 8, 23, 0, 0, 0, 0).getTime());
    expect(new Date(fimDoDia('2026-09-23')!).getTime()).toBe(new Date(2026, 8, 23, 23, 59, 59, 999).getTime());
  });
  it('campo vazio nao filtra', () => {
    expect(inicioDoDia('')).toBeUndefined();
    expect(fimDoDia('')).toBeUndefined();
  });
});

describe('listaDeAliases', () => {
  it('separa por vírgula, apara espaços e descarta vazios', () => {
    expect(listaDeAliases(' face  shield, viseira ,, ')).toEqual(['face shield', 'viseira']);
    expect(listaDeAliases('')).toEqual([]);
  });
});
