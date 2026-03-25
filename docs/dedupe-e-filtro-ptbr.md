# Dedupe e filtro pt-BR

## Objetivo

O catálogo do EIXO Leitura precisa buscar muito, filtrar duro e deduplicar forte antes de ativar qualquer item.

A regra de domínio é simples: o produto só sugere o que entrou com confiança suficiente como edição em português do Brasil.

## 1. Normalização

A normalização existe para reduzir ruído antes da deduplicação.

### Regras mínimas de normalização

Aplicar, no mínimo:

- caixa baixa;
- remoção de acentos;
- compactação de espaços;
- remoção de pontuação irrelevante;
- limpeza de ruído editorial recorrente;
- limpeza de subtítulos excessivos quando não ajudam a distinguir a edição.

### Exemplos de ruído a reduzir

- termos promocionais;
- variações tipográficas irrelevantes;
- sufixos editoriais redundantes;
- prefixos de coleção que não definem a obra;
- duplicação de espaços ou separadores.

### Resultado esperado

A normalização deve produzir, no mínimo:

- `normalized_title`
- `normalized_author`

Esses campos alimentam a camada intermediária de dedupe e os agrupamentos por obra.

## 2. Dedupe em camadas

A deduplicação não deve depender de uma única heurística.

Ela opera em três camadas.

### Camada A — ISBN

Regra:

- se `isbn10` ou `isbn13` convergir, tratar como forte candidato à mesma edição.

Uso:

- primeiro critério de união de edição;
- maior peso de confiança;
- base para atrelar múltiplos `source_records` à mesma `edition`.

Cuidados:

- ISBN ausente não impede ingestão;
- ISBN conflitante impede união automática;
- ISBN reutilizado de forma suspeita pede revisão ou permanência em staging.

### Camada B — título + autor normalizados

Regra:

- sem ISBN confiável, comparar `normalized_title` + `normalized_author`.

Uso:

- aproximar registros semanticamente equivalentes;
- localizar candidatos de `work` e, em alguns casos, de `edition`.

Quando pode unir edição:

- título normalizado converge fortemente;
- autor normalizado converge fortemente;
- demais sinais editoriais não entram em conflito relevante.

Quando não deve unir edição automaticamente:

- há divergência de editora, idioma ou formato que sugere edições distintas;
- o subtítulo muda o suficiente para indicar publicação diferente;
- o registro parece resumido demais para decisão segura.

### Camada C — agrupamento por obra

Regra:

- mesmo sem ISBN, registros que convergem fortemente para a mesma obra devem ser agrupados em `works`, preservando a separação de `editions` quando necessário.

Uso:

- unificar identidade canônica da obra;
- evitar múltiplas obras idênticas no banco por ruído entre fontes.

Quando unir obra:

- título e autor convergem de forma robusta;
- divergências remanescentes parecem de edição, não de obra;
- não há sinal forte de tradução independente, adaptação ou volume diferente.

Quando manter separado por segurança:

- dúvida entre obra original e adaptação;
- dúvida entre volume único e edição comentada que muda muito a identidade;
- dúvida entre autores homônimos;
- convergência parcial insuficiente.

## 3. Critérios de união e separação

### Une edição quando

- ISBN converge;
- ou título + autor normalizados convergem fortemente e os sinais editoriais são compatíveis;
- ou a nova fonte claramente reforça edição já existente.

### Une obra quando

- a convergência é forte no nível conceitual do livro;
- a divergência está no nível de editora, formato, data, ISBN ou marketplace;
- faz sentido manter múltiplas `editions` sob a mesma `work`.

### Mantém separado quando

- há conflito relevante de idioma;
- há conflito de autoria;
- há incerteza entre obra, adaptação ou volume;
- a diferença editorial pode alterar a identidade do item;
- a confiança é insuficiente para colapso seguro.

## 4. Estratégia de filtro pt-BR

A confiança pt-BR não deve depender de um único campo. Ela deve ser composta por sinais.

### Sinais positivos fortes

- `language_code = pt`;
- `language_region = BR`;
- editora brasileira conhecida;
- marketplace brasileiro;
- descrição claramente em português brasileiro;
- disponibilidade Kindle/Amazon Brasil quando isso reforçar a edição brasileira.

### Sinais positivos médios

- título e descrição em português;
- presença de metadados editoriais compatíveis com o mercado brasileiro;
- coincidência com edição já ativa em pt-BR.

### Sinais fracos ou insuficientes sozinhos

- apenas `language_code = pt` sem região;
- apenas marketplace genérico;
- descrição curta demais para inferência;
- ausência de ISBN, sem outros sinais fortes.

## 5. Estratégia de confiança pt-BR

A decisão recomendada é usar score composto com faixas operacionais.

### Faixa A — ativação segura

Condição:

- múltiplos sinais fortes convergem para pt-BR.

Ação:

- promover para `editions` com `is_pt_br_confident = true`;
- permitir que o item alimente o catálogo ativo.

### Faixa B — ambíguo útil

Condição:

- há sinais de português, mas a evidência de Brasil ainda é incompleta.

Ação:

- manter em staging;
- não ativar automaticamente;
- permitir reprocessamento futuro quando novas fontes reforçarem a confiança.

### Faixa C — baixa confiança

Condição:

- sinais insuficientes ou conflitantes.

Ação:

- descartar;
- ou manter apenas como registro não ativo para auditoria, sem alimentar o produto.

## 6. Tratamento de ambiguidade

Ambiguidade não deve virar ativação automática.

Se um registro for ambíguo, ele pode:

- permanecer em staging;
- ser marcado como `inactive`;
- ser descartado quando o ruído for evidente.

Casos típicos de ambiguidade:

- idioma `pt` sem evidência de `BR`;
- obra muito conhecida com múltiplas edições parecidas;
- fonte externa com metadados pobres;
- conflito entre marketplace e idioma declarado.

## 7. Papel específico da Amazon/Kindle no filtro pt-BR

Amazon/Kindle pode reforçar confiança, mas não deve decidir sozinha a identidade conceitual da obra.

Ela entra para:

- reforçar existência de edição Kindle;
- indicar contexto comercial brasileiro;
- enriquecer `availability_hint` e links preferenciais;
- atualizar sinais de mercado ao longo do tempo.

Ela não substitui os critérios de obra/edição já definidos no catálogo interno.

## 8. Ordem recomendada de processamento

1. receber registro cru em `staging_source_records`;
2. normalizar título e autor;
3. extrair sinais de idioma, região, editora e mercado;
4. rodar dedupe por ISBN;
5. rodar dedupe por título + autor normalizados;
6. decidir candidato de `work`;
7. decidir candidato de `edition`;
8. calcular confiança pt-BR;
9. promover, manter em staging ou descartar.

## 9. Regra de segurança final

Quando houver tensão entre escala e precisão, a arquitetura deve favorecer precisão.

Para o EIXO Leitura, é melhor ativar menos livros com alta confiança pt-BR do que poluir o catálogo ativo com registros errados, duplicados ou editorialmente ambíguos.
