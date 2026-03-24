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
python -m app.commands.catalog_pipeline ingest_google_books --query "literatura brasileira" --max-results 20
```

### 2) Ingestão Open Library

```bash
python -m app.commands.catalog_pipeline ingest_open_library --query "romance brasileiro" --max-results 20
```

### 3) Stub Amazon/Kindle

```bash
python -m app.commands.catalog_pipeline ingest_amazon_stub --query "kindle brasil"
```

### 4) Resumo de lote

```bash
python -m app.commands.catalog_pipeline summarize_ingestion_batch --batch-id 1
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
