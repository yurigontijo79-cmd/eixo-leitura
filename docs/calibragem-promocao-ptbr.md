# Calibragem da promoção pt-BR

## Problema observado

No pipeline inicial, parte dos lotes podia terminar com descarte em bloco, sem explicação operacional suficiente por registro. Isso dificultava distinguir:

- descarte duro por incompatibilidade real;
- retenção por ambiguidade legítima;
- bloqueio por colisão de dedupe;
- baixa confiança de pt-BR por falta de sinais.

## Causas mapeadas

1. decisão de promoção baseada apenas em faixa de score, com pouca granularidade de motivo;
2. falta de campos explícitos de decisão no staging;
3. resumo de lote com contagens globais, mas sem detalhamento por motivo;
4. inspeção limitada de exemplos por status de decisão.

## Explicabilidade adicionada

Cada `staging_source_record` passa a registrar:

- `decision_status` (`promoted`, `retained`, `discarded`);
- `decision_reason`;
- `pt_br_confidence_score`;
- `normalized_signals` (resumo de sinais usados na decisão);
- `staging_status` (mantido para compatibilidade).

Com isso, um registro descartado fica auditável: motivo, score e sinais principais ficam visíveis.

## Motivos de decisão possíveis nesta fase

### promoted

- `confianca_ptbr_alta`
- `open_library_sinais_fortes`
- `open_library_ptbr_textual`
- `sinais_ptbr_suficientes_sem_isbn`

### retained

- `ambiguidade_ptbr`
- `ambiguidade_sem_sinal_forte`
- `conflito_dedupe_revisar`

### discarded

- `idioma_incompativel`
- `metadado_insuficiente`
- `confianca_ptbr_insuficiente`
- `bloqueado_dedupe_colisao`

## Política calibrada de promote/retain/discard

A política continua conservadora, mas menos cega:

1. **descarta imediatamente** idioma incompatível explícito;
2. **descarta** metadado estruturalmente insuficiente;
3. **promove** score alto (`>= 70`) com segurança;
4. **para Open Library**, aceita promoção pragmática sem ISBN quando há sinais fortes suficientes (score alto + metadado textual consistente);
5. **não exige ISBN obrigatório** para promover quando sinais pt-BR e metadado textual já são fortes;
6. **retém** zona intermediária para ambiguidade útil e para conflito de dedupe que ainda requer revisão;
7. **descarta** score baixo (`< 35`) por confiança insuficiente.

## Ajustes feitos

- inclusão de `decision_status`, `decision_reason` e `normalized_signals` no staging;
- garantia operacional de `decision_reason` preenchido em novos registros;
- função de decisão explícita (`classify_catalog_decision`) separando idioma, metadado, confiança e dedupe;
- `summarize_ingestion_batch` com detalhamento por motivo de decisão;
- comandos de inspeção:
  - `inspect_ingestion_batch --batch-id X --limit N`
  - `inspect_staging_record --record-id X`

## Como inspecionar por lote

Comandos principais:

```bash
cd backend
python -m app.commands.catalog_pipeline summarize_ingestion_batch --batch-id <id>
python -m app.commands.catalog_pipeline inspect_ingestion_batch --batch-id <id> --limit 5
python -m app.commands.catalog_pipeline inspect_staging_record --record-id <record_id>
```

## Evidência operacional desta fase

Mesmo sob limitação de rede externa, os lotes ficam registrados com status e podem ser inspecionados. O resumo agora devolve:

- contagem por motivo de decisão;
- exemplos de retained;
- exemplos de discarded;
- promovidos (quando houver).

## Limitações conhecidas após calibragem

- o score pt-BR ainda é heurístico e inicial;
- Open Library pode vir com metadado incompleto;
- promoção sem ISBN continua dependente de sinais textuais e score forte (não é promoção automática);
- ambiente com bloqueio de rede pode gerar lotes `failed` sem coleta;
- a dedupe permanece conservadora e pragmática nesta etapa.
