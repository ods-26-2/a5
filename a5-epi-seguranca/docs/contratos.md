# Contratos assumidos para os mocks (a validar com os outros squads)

Estes payloads sao a MELHOR HIPOTESE do squad VER-3 para o que I9, S2, S3 e S4 vao
publicar, baseada no que esta descrito no documento de arquitetura. Quando B1
publicar os schemas oficiais, atualizar aqui e nos `integrations/*.py`.

## I9 -> A5 (estado por item)

```json
{
  "pessoa_id": "string",
  "zona_id": "string",
  "epi": "string",
  "estado": "correto | incorreto | ausente",
  "confianca": 0.0
}
```

## Zonas (cadastro interno do A5)

A zona e cadastrada no A5 (`/zonas`): `id`, `nome`, `descricao`, `camera_id`, `poligono`
(normalizado [0,1]) e `espaco_coordenadas`. A politica referencia a zona pelo `id` e guarda
um retrato dela em cada versao. Alterar o poligono/nome de uma zona com politica cria uma
nova versao da politica e reenvia o documento ao S2. Quando o S1 publicar o contrato de
zonas/cameras, este cadastro passa a ser alimentado por la (ver "Pontos a validar").

## A5 -> S2 (politica de violacao da zona)

Uma politica por zona, com **todos** os equipamentos exigidos nela. Cada alteracao
gera `version + 1` (as anteriores ficam so como historico; vale a ultima).
`class_aliases` leva, para cada equipamento exigido, os nomes de classe que o
detector pode emitir (comparacao sem distincao de caixa/acentos). A zona declara o
`coordinate_space` (V6/S1); o editor B6 exporta coordenadas normalizadas do quadro.

```json
{
  "policy_id": "obra-civil-sp",
  "version": 1,
  "person_class": "pessoa",
  "zone": {
    "id": "zona-producao-1",
    "name": "Producao 1",
    "coordinate_space": "image_normalized",
    "polygon": [{"x": 0.1, "y": 0.1}, {"x": 0.8, "y": 0.1}, {"x": 0.5, "y": 0.9}]
  },
  "required_equipment": [
    {"epi": "capacete", "tolerance_seconds": 10, "min_confidence": 0.6},
    {"epi": "luvas", "tolerance_seconds": 5, "min_confidence": 0.8}
  ],
  "class_aliases": {
    "capacete": ["capacete", "helmet", "hard hat"],
    "luvas": ["luva", "luvas", "glove", "gloves"]
  }
}
```

## S3 -> A5 (alerta qualificado)

```json
{
  "alerta_id": "string",
  "zona_id": "string",
  "pessoa_id": "string",
  "epi": "string",
  "severidade": "baixa | media | alta | critica",
  "criado_em": "ISO-8601",
  "deteccoes": [{"label": "string", "x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}]
}
```

`deteccoes` e opcional: caixas normalizadas [0,1] que o front desenha sobre o clipe
(player B6). Vem nos dados do evento, nao do S4.

## A5 -> S3 (comandos)

- `POST /alertas/{id}/ack` — reconhecimento (RF5)
- `POST /alertas/{id}/mute` — silenciamento temporario
- Desligamento manual completo (RF6) e decisao e registro **exclusivos do A5**,
  nao um comando enviado a S3 (mas pode evoluir para notificar S3 tambem).

## S4 -> A5 (evidencia)

```json
{
  "alerta_id": "string",
  "tipo": "imagem | clipe",
  "url_referencia": "string",
  "inicio_seg": 0.0,
  "fim_seg": 0.0,
  "pontos_de_interesse": [0.0]
}
```

Descritor de clipe do V6/S4: inicio, fim e pontos de interesse (instantes em segundos).
O S4 so recupera a midia; quem desenha caixas e rotulos e o player do B6.

## Pontos a validar com outros squads

- **S1/S2 (zona):** o V6 pede `coordinate_space` em toda zona e cita os modos *pixels* e
  *mundo*. O B6 exporta coordenadas **normalizadas** [0,1] do quadro. Validar se o S1 aceita
  esse espaco ou se o A5 deve converter para pixels (precisa da resolucao da camera).
- **S1 (camera):** `camera_id` da zona e um texto livre por enquanto; confirmar o identificador real.
- **S3 (`deteccoes`):** confirmar se o evento qualificado carrega as caixas.

## Envelope B1 (assumido)

Ver `src/a5/integrations/contracts/envelope.py`. Campos: origem, tempo_captura,
sessao, sequencia, confianca, versao_artefato, versao_schema.
