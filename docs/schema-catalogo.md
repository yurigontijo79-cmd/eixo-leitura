# Schema do catálogo canônico

## Princípio do schema

O schema do catálogo precisa separar:

- a obra (`works`);
- a edição (`editions`);
- a origem externa (`source_records`);
- a ingestão temporária (`staging`).

Essa separação impede que um registro cru de marketplace vire, por acidente, a identidade da obra dentro do produto.

## Visão geral das tabelas

### Catálogo principal

- `works`
- `editions`
- `source_records`

### Staging

- `ingestion_batches`
- `staging_source_records`

## 1. `works`

Representa a obra em nível canônico.

### Campos obrigatórios

- `id`
- `canonical_title`
- `canonical_author`
- `normalized_title`
- `normalized_author`
- `language_primary`
- `is_active`
- `created_at`
- `updated_at`

### Campos opcionais recomendados

- `canonical_subtitle`
- `author_sort`
- `work_cluster_key`
- `notes_internal`

### Chaves e índices recomendados

- PK: `id`
- índice por `normalized_title`
- índice por `normalized_author`
- índice composto por `normalized_title + normalized_author`
- índice opcional por `work_cluster_key`

### Papel da tabela

- consolidar a identidade da obra;
- permitir agrupamento de múltiplas edições;
- servir como base estável para curadoria interna.

## 2. `editions`

Representa uma edição específica vinculada a uma obra.

### Campos obrigatórios

- `id`
- `work_id`
- `edition_title`
- `publisher`
- `format_type`
- `language_code`
- `is_pt_br_confident`
- `created_at`
- `updated_at`

### Campos opcionais recomendados

- `subtitle`
- `published_date`
- `isbn10`
- `isbn13`
- `language_region`
- `cover_url`
- `market_country`
- `kindle_available`
- `pt_br_confidence_score`
- `activation_status`
- `activated_at`
- `deactivated_at`

### Chaves e índices recomendados

- PK: `id`
- FK: `work_id -> works.id`
- índice por `isbn10`
- índice por `isbn13`
- índice por `language_code + language_region`
- índice por `activation_status`
- índice por `is_pt_br_confident`

### Papel da tabela

- guardar a edição usada pelo produto;
- separar diferentes formatos e publicações da mesma obra;
- concentrar os sinais que definem ativação pt-BR.

## 3. `source_records`

Representa a aparição da edição em cada fonte externa.

### Campos obrigatórios

- `id`
- `edition_id`
- `source_name`
- `source_record_id`
- `source_payload_json`
- `fetched_at`
- `last_seen_at`

### Campos opcionais recomendados

- `source_url`
- `availability_hint`
- `kindle_available`
- `marketplace_country`
- `source_confidence_score`
- `is_current`

### Chaves e índices recomendados

- PK: `id`
- FK: `edition_id -> editions.id`
- UNIQUE recomendado: `source_name + source_record_id`
- índice por `edition_id`
- índice por `source_name`
- índice por `last_seen_at`

### Papel da tabela

- manter rastreabilidade completa da origem;
- permitir atualização periódica por fonte;
- preservar payload cru para auditoria e reprocessamento.

## 4. `ingestion_batches`

Representa cada rodada de ingestão externa.

### Campos obrigatórios

- `id`
- `source_name`
- `started_at`
- `status`

### Campos opcionais recomendados

- `finished_at`
- `query_context`
- `records_fetched`
- `records_promoted`
- `records_discarded`
- `error_summary`

### Papel da tabela

- rastrear lotes de ingestão;
- permitir auditoria mínima;
- sustentar reprocessamento por lote quando necessário.

## 5. `staging_source_records`

Representa o registro externo antes da promoção ao catálogo principal.

### Campos obrigatórios

- `id`
- `ingestion_batch_id`
- `source_name`
- `source_record_id`
- `raw_payload_json`
- `raw_title`
- `raw_author`
- `fetched_at`

### Campos opcionais recomendados

- `raw_subtitle`
- `raw_publisher`
- `raw_language_code`
- `raw_language_region`
- `raw_isbn10`
- `raw_isbn13`
- `raw_source_url`
- `normalized_title`
- `normalized_author`
- `dedupe_candidate_work_id`
- `dedupe_candidate_edition_id`
- `pt_br_confidence_score`
- `pt_br_confidence_reason`
- `staging_status`
- `discard_reason`

### Chaves e índices recomendados

- PK: `id`
- FK: `ingestion_batch_id -> ingestion_batches.id`
- índice por `source_name + source_record_id`
- índice por `normalized_title + normalized_author`
- índice por `staging_status`
- índice por `pt_br_confidence_score`

### Papel da tabela

- concentrar a fase de normalização e decisão;
- manter registros ambíguos fora do catálogo ativo;
- apoiar dedupe e ativação com segurança.

## Relacionamentos principais

A relação canônica é:

- uma `work` possui muitas `editions`;
- uma `edition` possui muitos `source_records`;
- um `ingestion_batch` possui muitos `staging_source_records`;
- um `staging_source_record` pode apontar, durante a análise, para candidatos de `work` e `edition`, mas sem promoção automática.

## O que é persistido

É persistido:

- identidade canônica da obra;
- dados específicos da edição;
- rastreabilidade por fonte externa;
- lotes de ingestão;
- staging crua e normalizada;
- status de ativação e descarte.

## O que é derivado

É derivado ou recalculável:

- score de confiança pt-BR;
- chave de normalização;
- candidatos de dedupe;
- decisão final de promoção;
- visões do catálogo ativo consumidas pelo produto.

## Campos de ativação recomendados

Para não misturar domínio editorial com ingestão, recomenda-se que a tabela `editions` concentre o estado final de exposição ao produto.

Campos recomendados:

- `activation_status`
- `is_pt_br_confident`
- `pt_br_confidence_score`
- `activated_at`
- `deactivated_at`

## Regra de segurança do schema

Se houver dúvida entre unir ou separar, o schema deve favorecer separação temporária.

É melhor manter duas edições próximas separadas por segurança do que colapsar, cedo demais, registros distintos em uma única identidade canônica.
