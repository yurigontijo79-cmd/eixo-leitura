# Ingestão local real (hardened)

## Objetivo

Este guia descreve como executar ingestão real em ambiente local com maior resiliência operacional para Google Books e Open Library.

## Variáveis de ambiente suportadas

- `GOOGLE_BOOKS_API_KEY`
- `OPENLIBRARY_USER_AGENT`
- `INGEST_TIMEOUT_SECONDS`
- `GOOGLE_BOOKS_RETRY_MAX`
- `GOOGLE_BOOKS_BACKOFF_SECONDS`
- `OPENLIBRARY_THROTTLE_SECONDS`

## Configuração sugerida (shell)

```bash
export GOOGLE_BOOKS_API_KEY="<sua-chave>"
export OPENLIBRARY_USER_AGENT="EIXOLeituraCatalogBot/0.1 (+contato-local)"
export INGEST_TIMEOUT_SECONDS=25
export GOOGLE_BOOKS_RETRY_MAX=3
export GOOGLE_BOOKS_BACKOFF_SECONDS=2.0
export OPENLIBRARY_THROTTLE_SECONDS=0.6
```

## Rodada mínima recomendada

Comece pequeno para validar rede, quota e parsing:

```bash
cd backend
python -m app.commands.catalog_pipeline ingest_google_books --query "literatura brasileira" --max-results 5 --source-timeout 25 --retry-max 3 --backoff-seconds 2.0
python -m app.commands.catalog_pipeline ingest_open_library --query "romance brasileiro" --max-results 5 --source-timeout 25 --throttle-seconds 0.6
```

## Execução em lote por seeds (recomendado para povoamento inicial)

Arquivo inicial sugerido no repositório:

- `seeds/seeds_ptbr_iniciais.txt`

Formato do arquivo:

- uma seed por linha;
- linhas vazias são ignoradas;
- linhas iniciadas por `#` são comentários.

### Batch Google Books

```bash
cd backend
python -m app.commands.catalog_pipeline ingest_seed_list \
  --source google_books \
  --seed-file ../seeds/seeds_ptbr_iniciais.txt \
  --max-results 10 \
  --seed-throttle-seconds 1.2 \
  --source-timeout 25 \
  --retry-max 3 \
  --backoff-seconds 2.0
```

### Batch Open Library

```bash
cd backend
python -m app.commands.catalog_pipeline ingest_seed_list \
  --source open_library \
  --seed-file ../seeds/seeds_ptbr_iniciais.txt \
  --max-results 10 \
  --seed-throttle-seconds 0.6 \
  --source-timeout 25 \
  --throttle-seconds 0.5
```

### Flags úteis de operação

- `--max-results` (default `10`; recomendado entre 5 e 20)
- `--seed-limit` (rodada parcial para teste)
- `--seed-throttle-seconds` (cadência entre seeds)
- `--source-timeout`
- Google: `--retry-max`, `--backoff-seconds`
- Open Library: `--throttle-seconds`

## Como interpretar erros comuns

### 429 (Too Many Requests)
- indica rate limit/quota da fonte;
- o Google Books já aplica retry com backoff simples;
- reduza `max-results` e aumente backoff quando necessário.

### 403
- pode indicar bloqueio de proxy/túnel, chave inválida ou política da fonte;
- valide `GOOGLE_BOOKS_API_KEY`;
- valide conectividade sem proxy corporativo restritivo.

### Timeout
- aumente `INGEST_TIMEOUT_SECONDS` ou use `--source-timeout`;
- rode lotes menores para reduzir tempo de resposta.

### Resposta vazia / parsing
- tente query alternativa mais simples;
- confirme se a fonte respondeu payload JSON válido no ambiente local.

## Estratégia segura antes de povoamento maior

1. executar 2-3 lotes pequenos;
2. usar `summarize_ingestion_batch` e `inspect_ingestion_batch`;
3. validar decisão por motivo (`decision_reason`);
4. só então aumentar `max-results` gradualmente.

## Como interpretar o resumo consolidado do batch

Ao final, o comando retorna JSON com:

- `seed_count_processed`
- `batches_created`
- `records_fetched_total`
- `records_promoted_total`
- `records_retained_total`
- `records_discarded_total`
- `seeds_failed`
- `seeds_with_promoted`
- `seeds_without_promoted`

Além disso, `results` traz resultado por seed:

- `seed`
- `batch_id`
- `status`
- `records_fetched/promoted/retained/discarded`
- `error` (quando houver)

## Retomar após falha parcial

Se parte das seeds falhar:

1. identifique seeds com `status != completed` no `results`;
2. crie um novo arquivo com somente essas seeds;
3. rode novamente `ingest_seed_list` com o arquivo reduzido;
4. inspecione os `batch_id` problemáticos via `summarize_ingestion_batch` e `inspect_ingestion_batch`.

## Limitações remanescentes

- resiliência ainda é pragmática, não distribuída;
- variações de rede/proxy local podem bloquear fontes mesmo com retry;
- Open Library depende de metadado frequentemente incompleto para idioma/região.
