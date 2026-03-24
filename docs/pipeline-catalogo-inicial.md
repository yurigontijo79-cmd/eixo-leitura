# Pipeline inicial do catálogo

## Escopo desta fase

Esta fase implementa a primeira versão funcional do povoamento do catálogo interno do EIXO Leitura.

O produto continua sugerindo livros a partir de banco próprio. A ingestão externa ocorre fora do fluxo de navegação, via pipeline com staging e promoção controlada.

## Fontes integradas nesta versão

1. **Google Books** (fonte principal da ingestão inicial).
2. **Open Library** (fonte complementar).
3. **Amazon/Kindle** como **stub técnico** nesta fase (interface preparada, sem ingestão real obrigatória).

## Fluxo implementado

1. abre lote em `ingestion_batches` com `source_name`, `started_at` e `status`;
2. busca registros reais na fonte externa escolhida;
3. grava payload cru e metadados em `staging_source_records`;
4. normaliza título/autor;
5. calcula confiança pt-BR inicial;
6. aplica dedupe conservadora (ISBN forte e convergência básica título+autor);
7. promove apenas registros com confiança e convergência suficientes;
8. fecha lote com totais de coletados, promovidos, retidos e descartados.

## Estruturas usadas

### Catálogo principal

- `works`
- `editions`
- `source_records`

### Ingestão e staging

- `ingestion_batches`
- `staging_source_records`

### Convivência temporária com catálogo existente

- tabela `books` segue ativa para o app;
- registros externos promovidos geram/atualizam entradas em `books` com `source_type='external'`;
- registros mockados permanecem com `source_type='mock'`;
- seleção de catálogo usada pelo app pode ser controlada por `EIXO_CATALOG_SOURCE` (`mock`, `real`, `mixed`).

## Dedupe inicial implementada

Ordem aplicada na promoção:

1. ISBN-13 (chave forte de edição);
2. ISBN-10 (chave forte de edição);
3. título+autor normalizados (convergência básica);
4. separação por segurança quando não houver convergência suficiente.

A dedupe desta versão é pragmática, real e conservadora.

## Filtro pt-BR inicial implementado

O pipeline calcula score inicial com sinais como:

- `language_code=pt`;
- `language_region=BR` quando disponível;
- editora com sinal brasileiro;
- texto com indício de português;
- marketplace brasileiro (quando presente no link da fonte).

Resultado operacional nesta versão:

- `score >= 60`: promove;
- `40 <= score < 60`: retém em staging;
- `score < 40`: descarta.

## Promoção ao catálogo ativo

Quando promovido:

- encontra ou cria `work`;
- encontra ou cria `edition` ativa com confiança pt-BR;
- cria/atualiza `source_record` rastreável;
- cria/atualiza entrada em `books` com `source_type='external'` e `is_catalog_active=1`.

## Observabilidade mínima

O pipeline já permite inspecionar por lote:

- total coletado;
- total promovido;
- total retido;
- total descartado;
- exemplos de livros/edições promovidos.

Essa inspeção é feita por comando de terminal (`summarize_ingestion_batch`).

## Limitações conhecidas desta primeira versão

- dedupe ainda heurística e conservadora (sem reconciliação avançada);
- score pt-BR inicial, com sinais simples;
- Amazon/Kindle ainda em modo stub técnico;
- sem painel visual de administração;
- sem execução agendada de ingestão (rodagem manual por comando).


## Explicabilidade de decisão (calibragem fase 15)

Cada item de staging agora registra:

- `decision_status`;
- `decision_reason`;
- `pt_br_confidence_score`;
- `normalized_signals`.

Isso permite auditoria por registro e diagnóstico por lote sem dashboard.
