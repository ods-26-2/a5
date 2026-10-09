// Espelha os modelos do backend (src/a5/modules/*/models.py e api/*).

export type Severidade = 'baixa' | 'media' | 'alta' | 'critica';
export type Papel = 'operador' | 'supervisor' | 'auditor' | 'administrador';

export interface Ponto { x: number; y: number }
export interface Zona {
  id: string;
  nome?: string | null;
  poligono?: Ponto[];
  espaco_coordenadas?: 'imagem_normalizada'; // o editor B6 exporta coordenadas normalizadas [0,1]
}

export interface ZonaCadastro {
  id: string;
  nome: string | null;
  descricao: string | null;
  camera_id: string | null;
  espaco_coordenadas: string;
  poligono: Ponto[];
  ativa: boolean;
  atualizada_em: string;
}
export interface NovaZona {
  id: string;
  nome?: string | null;
  descricao?: string | null;
  camera_id?: string | null;
  poligono?: Ponto[];
}
/** Campos ausentes ficam como estao; poligono [] remove a geometria. */
export interface AtualizarZona {
  nome?: string | null;
  descricao?: string | null;
  camera_id?: string | null;
  poligono?: Ponto[];
  ativa?: boolean;
}

export interface Turno { zona_id?: string; inicio: string; fim: string }

export interface Usuario { id: string; nome: string; papel: Papel; ativo: boolean }
export interface NovoUsuario { id: string; nome: string; papel: Papel; senha?: string }
export interface AtualizarUsuario { nome?: string; papel?: Papel; ativo?: boolean; senha?: string }
export interface SessaoApi { token: string; usuario: Usuario }

export interface EPI { id: string; nome: string; ativo: boolean; aliases: string[] }

export interface EquipamentoExigido {
  epi_id: string;
  tempo_tolerancia_segundos: number | null; // null = herda o padrao da politica
  confianca_minima: number | null;
}

export interface NovaPolitica {
  id?: string | null;
  zona: Zona;
  classe_pessoa: string;
  equipamentos_obrigatorios: EquipamentoExigido[];
  tempo_tolerancia_segundos: number;
  confianca_minima: number;
}

export interface NovoEPI { id: string; nome: string; aliases: string[] }
export interface AtualizarEPI { nome?: string; aliases?: string[]; ativo?: boolean }

export interface Politica extends NovaPolitica {
  id: string;
  versao: number;
  criada_em: string;
}

export interface Deteccao { label: string; x: number; y: number; width: number; height: number }

export interface Ocorrencia {
  alerta_id: string;
  zona_id: string;
  pessoa_id: string;
  epi: string;
  severidade: Severidade;
  descricao: string;
  evidencia_url: string | null;
  evidencia_inicio_seg: number | null;
  evidencia_fim_seg: number | null;
  em_violacao_ha_segundos: number | null;
  deteccoes: Deteccao[];
}

export interface Alerta {
  alerta_id: string;
  zona_id: string;
  pessoa_id: string;
  epi: string;
  severidade: Severidade;
  criado_em: string;
  reconhecido: boolean;
  silenciado: boolean;
}

export interface EstadoItem {
  pessoa_id: string;
  zona_id: string;
  epi: string;
  estado: 'correto' | 'incorreto' | 'ausente';
  confianca: number;
  /** RNF2: 'incerta' = duvida (nao vira acao automatica). */
  classificacao?: 'baixa' | 'incerta' | 'alta';
}

export interface Registro {
  alerta_id: string;
  usuario: string;
  registrado_em: string;
  tipo: 'ack' | 'mute' | 'desligamento';
  zona_id: string | null;
  epi: string | null;
  evidencia_url: string | null;
  evidencia_inicio_seg: number | null;
  evidencia_fim_seg: number | null;
}

export interface FiltroHistorico {
  zona?: string;
  usuario?: string;
  tipo?: string;
  desde?: string; // ISO-8601
  ate?: string;
}

export interface Relatorio {
  zona_id: string;
  total: number;
  por_severidade: Record<string, number>;
  por_epi: Record<string, number>;
}

export type Saude = Record<string, string>;
