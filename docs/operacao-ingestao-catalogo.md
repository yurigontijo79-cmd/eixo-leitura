# Operação da ingestão de catálogo

## Pré-requisitos

- backend configurado com dependências instaladas;
- acesso de rede para Google Books e Open Library;
- banco SQLite inicializado (o próprio comando já inicializa se necessário).

## Comandos disponíveis

A execução é feita via módulo Python:

```bash
cd backend
python -m app.commands.catalog_pipeline <comando>
```

### 1) Ingestão Google Books

```bash
python -m app.commands.catalog_pipeline ingest_google_books --query "literatura brasileira" --max-results 20 --source-timeout 25 --retry-max 3 --backoff-seconds 2.0
```

### 2) Ingestão Open Library

```bash
python -m app.commands.catalog_pipeline ingest_open_library --query "romance brasileiro" --max-results 20 --source-timeout 25 --throttle-seconds 0.6
```

### 3) Stub Amazon/Kindle

```bash
python -m app.commands.catalog_pipeline ingest_amazon_stub --query "kindle brasil"
```

### 4) Resumo de lote

```bash
python -m app.commands.catalog_pipeline summarize_ingestion_batch --batch-id 1
```

### 5) Inspeção detalhada de lote

```bash
python -m app.commands.catalog_pipeline inspect_ingestion_batch --batch-id 1 --limit 5
```

### 6) Inspeção de registro de staging

```bash
python -m app.commands.catalog_pipeline inspect_staging_record --record-id 1
```

### 7) Ingestão em lote por arquivo de seeds

```bash
python -m app.commands.catalog_pipeline ingest_seed_list \
  --source google_books \
  --seed-file ../seeds/seeds_ptbr_iniciais.txt \
  --max-results 10 \
  --seed-throttle-seconds 1.2 \
  --source-timeout 25 \
  --retry-max 3 \
  --backoff-seconds 2.0
```

Exemplo Open Library:

```bash
python -m app.commands.catalog_pipeline ingest_seed_list \
  --source open_library \
  --seed-file ../seeds/seeds_ptbr_iniciais.txt \
  --max-results 10 \
  --seed-throttle-seconds 0.6 \
  --source-timeout 25 \
  --throttle-seconds 0.5
```

## Saída esperada

Os comandos de ingestão retornam JSON com:

- `batch_id`
- `source_name`
- `status`
- `records_fetched`
- `records_promoted`
- `records_retained`
- `records_discarded`
- `examples`
- `decision_breakdown`
- `retained_examples`
- `discarded_examples`

## Como staging e promoção funcionam

- todo registro externo entra em `staging_source_records` com payload cru;
- o pipeline calcula score pt-BR e status (`promoted`, `retained`, `discarded`);
- somente `promoted` vira `edition` ativa e entra no catálogo do app.

## Como inspecionar resultados

Passos mínimos:

1. rodar ingestão;
2. capturar `batch_id` do JSON de saída;
3. rodar `summarize_ingestion_batch`;
4. validar totais e exemplos promovidos.

No modo batch (`ingest_seed_list`), o próprio retorno já inclui resumo consolidado e resultados por seed.

## Convivência mock x real no app

Variável de ambiente:

- `EIXO_CATALOG_SOURCE=mock` → app lê somente mock;
- `EIXO_CATALOG_SOURCE=real` → app lê somente catálogo externo promovido;
- `EIXO_CATALOG_SOURCE=mixed` (padrão) → app lê ambos ativos.

## Exemplo de execução funcional (lote real)

Exemplo de rodada local esperada:

1. `ingest_google_books --query "literatura brasileira" --max-results 10`
2. saída com lote concluído e parte dos itens promovidos;
3. `summarize_ingestion_batch --batch-id <id_retornado>`
4. visualização dos totais e de exemplos de obras/edições ativadas.

## Limitações conhecidas da operação nesta fase

- qualidade da promoção depende dos metadados da fonte;
- não há agendamento automático;
- Open Library pode retornar menos sinais de idioma/região;
- Amazon está somente como stub técnico.

## Comportamento em bloqueio de rede

Se a fonte externa estiver indisponível (por exemplo, proxy bloqueando acesso), o lote é encerrado com `status=failed` e o erro fica registrado no retorno do comando de ingestão.

Mesmo em falha, o lote permanece consultável por `summarize_ingestion_batch`.

No batch, falhas parciais não interrompem a rodada inteira: cada seed gera seu próprio lote e erro associado no relatório final.


## Variáveis de ambiente para hardening

- `GOOGLE_BOOKS_API_KEY`
- `OPENLIBRARY_USER_AGENT`
- `INGEST_TIMEOUT_SECONDS`
- `GOOGLE_BOOKS_RETRY_MAX`
- `GOOGLE_BOOKS_BACKOFF_SECONDS`
- `OPENLIBRARY_THROTTLE_SECONDS`

Veja também `docs/ingestao-local-real.md`.

## Formato do arquivo de seeds

- um termo por linha;
- linhas vazias são ignoradas;
- linhas iniciadas com `#` são tratadas como comentário.

Exemplo:

```text
literatura brasileira
romance brasileiro
clarice lispector
# comentário
```

## Flags principais do `ingest_seed_list`

- `--source` (`google_books` | `open_library`)
- `--seed-file` (caminho do arquivo de seeds)
- `--max-results` (default `10`)
- `--seed-limit` (limite opcional de seeds processadas)
- `--seed-throttle-seconds` (pausa entre seeds)
- `--source-timeout`
- `--retry-max` e `--backoff-seconds` (Google Books)
- `--throttle-seconds` (Open Library)

## Resumo consolidado do batch

O retorno final inclui:

- `seed_count_processed`
- `batches_created`
- `records_fetched_total`
- `records_promoted_total`
- `records_retained_total`
- `records_discarded_total`
- `seeds_failed`
- `seeds_with_promoted`
- `seeds_without_promoted`

Também há `results` com saída por seed (`batch_id`, `status`, totais e `error` quando existir).
