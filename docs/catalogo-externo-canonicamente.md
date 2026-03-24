# Arquitetura canônica do catálogo externo

## Objetivo desta arquitetura

O catálogo mockado do MVP serviu para validar o produto, mas deixa de ser suficiente como base real do EIXO Leitura.

O produto precisa continuar sugerindo livros a partir de banco próprio, com estabilidade, previsibilidade e controle editorial mínimo. Ao mesmo tempo, esse banco não deve depender de cadastro manual integral nem de consulta crua a APIs externas a cada clique.

A arquitetura canônica resolve essa transição com uma regra simples:

- o produto sugere a partir de catálogo interno ativo;
- o catálogo interno é povoado e atualizado por fontes externas;
- registros crus de API não entram diretamente na experiência do usuário;
- só entram no catálogo ativo itens com confiança suficiente de edição em português do Brasil.

## Por que o catálogo mockado deixa de ser suficiente

O mock atual é útil para validação de fluxo, mas não sustenta:

- cobertura ampla;
- atualização periódica;
- múltiplas edições da mesma obra;
- controle forte de idioma e região;
- deduplicação entre fontes externas;
- separação clara entre obra, edição e origem.

Se o produto dependesse do mock como fonte real, ele ficaria limitado demais para curadoria, ingestão futura e manutenção do catálogo.

## Princípio operacional do novo catálogo

O EIXO Leitura não consultará Google Books, Open Library ou Amazon/Kindle a cada clique da home.

O fluxo correto é:

1. buscar dados externamente;
2. armazenar em staging;
3. normalizar;
4. aplicar filtro pt-BR;
5. deduplicar em camadas;
6. ativar apenas o que atingir confiança suficiente;
7. expor ao produto apenas o catálogo interno ativo.

Com isso, a experiência continua rápida, previsível e baseada em banco próprio.

## Fontes externas e seus papéis

### Google Books

Papel canônico: fonte principal de metadados e escala.

Uso esperado:

- alta cobertura de títulos;
- boa disponibilidade de metadados básicos;
- ponto de partida para descoberta ampla;
- alimentação principal da camada de staging.

### Open Library

Papel canônico: fonte complementar de cobertura, enriquecimento e descoberta.

Uso esperado:

- ampliar cobertura onde o Google Books vier incompleto;
- reforçar metadados bibliográficos;
- ajudar na convergência entre obra e edição.

### Amazon/Kindle

Papel canônico: fonte complementar de edição e mercado.

Uso esperado:

- enriquecer disponibilidade comercial;
- reforçar sinais de edição Kindle;
- capturar link preferencial de compra quando fizer sentido;
- reforçar confiança de mercado brasileiro quando houver Amazon Brasil.

Amazon não define soberanamente a obra. Ela entra como reforço de edição, disponibilidade e contexto comercial.

## Modelo conceitual canônico

A arquitetura separa três camadas principais e uma camada de staging.

### 1. `works`

Representa a obra em si.

É o nível conceitual do título, independente de editora, ISBN ou marketplace específico.

### 2. `editions`

Representa uma edição específica da obra.

É o nível onde ficam ISBN, editora, idioma da edição, formato e sinais de confiança pt-BR.

### 3. `source_records`

Representa como aquela edição apareceu em uma fonte externa específica.

É o nível de rastreabilidade. Permite saber de onde veio cada metadado, quando foi visto e qual payload cru o originou.

### 4. `staging`

Representa a camada intermediária de ingestão.

Ela existe para receber registros crus, normalizar, filtrar, deduplicar e decidir ativação, sem contaminar imediatamente o catálogo ativo.

## Estratégia de staging

A staging deve ser simples, explícita e suficiente para auditoria mínima.

Estrutura recomendada:

- `ingestion_batches`: identifica cada execução de coleta/importação;
- `staging_source_records`: guarda registros crus ou semicurados antes da ativação.

Funções da staging:

- receber o payload cru da fonte externa;
- manter rastreabilidade por lote;
- registrar sinais de linguagem, região e mercado;
- armazenar normalizações intermediárias;
- executar heurísticas de dedupe sem afetar o catálogo ativo;
- classificar cada registro como ativável, ambíguo, descartado ou pendente.

## Ativação no catálogo principal

A ativação não deve ser automática por mera presença em fonte externa.

Para entrar no catálogo ativo, o registro precisa:

- convergir com obra e edição válidas;
- ter confiança suficiente de pt-BR na edição;
- não colidir de forma insegura com edição já existente;
- carregar rastreabilidade suficiente para revisão futura.

Estados operacionais recomendados para a decisão de catálogo:

- `active`: edição apta a alimentar o produto;
- `inactive`: registro persistido, mas não exposto ao produto;
- `staging_only`: ainda não promovido;
- `discarded`: rejeitado por baixa confiança ou ruído.

## Como o catálogo ativo alimenta o produto

O produto continuará sugerindo a partir de banco interno ativo.

Na prática:

- a home consulta o catálogo próprio do EIXO Leitura;
- a lógica de sugestões continua operando sobre estados internos e histórico do leitor;
- o pipeline externo apenas povoa e atualiza a base;
- nenhuma tela do produto depende de latência ou disponibilidade da API externa em tempo real.

## Regra-mãe do catálogo ativo

A regra central desta arquitetura é:

> só entram no catálogo ativo itens com confiança suficiente de edição em português do Brasil.

Isso protege o produto contra:

- mistura de edições em idiomas errados;
- duplicação excessiva;
- registros crus de baixa qualidade;
- dependência conceitual de fontes externas como verdade final.

## Decisões de domínio que ficam travadas nesta fase

Esta arquitetura fixa as seguintes travas:

- o catálogo do produto será interno e canônico;
- ingestão externa serve a povoamento e atualização, não à experiência direta;
- obra, edição e origem permanecem separadas;
- staging é obrigatória;
- dedupe será forte e em camadas;
- ativação depende de confiança pt-BR;
- ambiguidade não entra automaticamente no catálogo ativo.

## O que não será implementado nesta fase

Fica fora desta entrega:

- pipeline completo de ingestão;
- chamadas reais às APIs externas;
- repovoamento massivo do banco;
- telas novas do produto;
- expansão da UX;
- IA ou busca semântica;
- múltiplos usuários e autenticação.

A fase atual é de arquitetura, schema e travas de domínio.
