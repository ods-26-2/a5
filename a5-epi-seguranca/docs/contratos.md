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

## A5 -> S2 (parametros da politica de violacao)

```json
{
  "epi": "string",
  "zona_id": "string",
  "tempo_tolerancia_segundos": 0,
  "confianca_minima": 0.0
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
  "criado_em": "ISO-8601"
}
```

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
  "fim_seg": 0.0
}
```

## Envelope B1 (assumido)

Ver `src/a5/integrations/contracts/envelope.py`. Campos: origem, tempo_captura,
sessao, sequencia, confianca, versao_artefato, versao_schema.
