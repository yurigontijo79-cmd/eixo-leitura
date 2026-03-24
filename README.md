# EIXO Leitura

EIXO Leitura é um MVP de leitura guiada com memória de percurso. O produto ajuda a escolher por onde começar, guardar livros para depois, registrar sessões curtas, responder reflexões breves e encerrar leituras com uma memória mínima do caminho.

## Visão do produto

O foco do MVP não é entregar ebook, produtividade ou gamificação. O foco é sustentar um percurso de leitura com mediação discreta, poucos estados e regras simples.

## Documentos canônicos

A documentação principal do MVP está nestes arquivos:

- `docs/mvp-canonico.md` — definição do que o produto é, o que não é, seu escopo oficial e o estado canônico atual;
- `docs/arquitetura.md` — arquitetura real do MVP, stack, entidades, persistência, dados derivados e responsabilidades por camada;
- `docs/fluxos-do-produto.md` — fluxos centrais do produto, do primeiro contato à conclusão da leitura;
- `docs/proximos-passos-controlados.md` — o que pode evoluir com segurança e o que deve permanecer fora desta fase;
- `docs/catalogo-externo-canonicamente.md` — arquitetura do catálogo interno canônico povoado por fontes externas;
- `docs/schema-catalogo.md` — schema conceitual do catálogo com separação entre obra, edição, origem e staging;
- `docs/dedupe-e-filtro-ptbr.md` — regras de normalização, dedupe em camadas e ativação por confiança pt-BR;
- `docs/pipeline-catalogo-inicial.md` — desenho e implementação da primeira versão funcional do pipeline de povoamento;
- `docs/operacao-ingestao-catalogo.md` — comandos operacionais para ingestão, promoção e inspeção por lote;
- `docs/runbook-local.md` — operação local curta, portas sugeridas e resolução rápida de problemas;
- `docs/validacao-mvp-local.md` — registro objetivo da validação guiada do MVP em uso local;
- `docs/overview.md` — índice curto de apoio para a base canônica.

## Arquitetura do catálogo interno

O produto continuará sugerindo livros a partir de banco próprio. A nova arquitetura canônica do catálogo define que:

- o catálogo ativo do produto é interno;
- fontes externas povoam e atualizam esse catálogo, mas não alimentam a home em tempo real;
- a modelagem separa `works`, `editions` e `source_records`;
- a ingestão passa por staging antes de qualquer ativação;
- só entram no catálogo ativo itens com confiança suficiente de edição em português do Brasil.

Para esse desenho, consultar:

- `docs/catalogo-externo-canonicamente.md`
- `docs/schema-catalogo.md`
- `docs/dedupe-e-filtro-ptbr.md`


## Pipeline inicial de catálogo externo

O pipeline inicial foi implementado para povoar o catálogo interno sem consulta externa em tempo real no fluxo da home.

Comandos principais (backend):

```bash
cd backend
python -m app.commands.catalog_pipeline ingest_google_books --query "literatura brasileira" --max-results 20
python -m app.commands.catalog_pipeline ingest_open_library --query "romance brasileiro" --max-results 20
python -m app.commands.catalog_pipeline summarize_ingestion_batch --batch-id 1
```

Controle de convivência mock/real no app:

- `EIXO_CATALOG_SOURCE=mock`
- `EIXO_CATALOG_SOURCE=real`
- `EIXO_CATALOG_SOURCE=mixed` (padrão)

Detalhes completos em `docs/pipeline-catalogo-inicial.md` e `docs/operacao-ingestao-catalogo.md`.

## Como rodar

### Backend

Porta sugerida: `8000`.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verificação mínima:

```bash
curl http://127.0.0.1:8000/health
```

### Frontend

Porta sugerida: `5173`. Endereço sugerido de acesso local: `http://127.0.0.1:5173`.

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Configuração de `VITE_API_URL`

Por padrão, o frontend espera a API em `http://127.0.0.1:8000`.

Se quiser explicitar a variável antes de subir o frontend:

```bash
cd frontend
export VITE_API_URL=http://127.0.0.1:8000
npm run dev -- --host 127.0.0.1 --port 5173
```

Se a API estiver em outra porta, ajuste a variável para o endereço correspondente.

## Fluxo mínimo de teste manual

1. subir o backend e confirmar `GET /health` com status `ok`;
2. subir o frontend com `VITE_API_URL` apontando para a API correta;
3. abrir a home e verificar sugestões e shortlist vazia ou existente;
4. abrir um livro e movê-lo para `current` ou `shortlist`;
5. registrar uma sessão na tela de leitura atual;
6. responder a reflexão curta quando disponível;
7. verificar a devolutiva mínima e a trajetória da leitura;
8. concluir a leitura e confirmar o livro em `Concluídos`;
9. voltar para a home e verificar a reabertura do ciclo para o próximo livro.

## Estado atual do MVP

O núcleo canônico já está implementado e cobre:

- sugestões iniciais com memória de percurso;
- shortlist;
- leitura atual;
- sessões de leitura;
- reflexões curtas;
- devolutiva mínima;
- trajetória da leitura;
- conclusão da leitura;
- livros concluídos;
- transição para o próximo livro;
- lapidação mínima de UX e microtexto.

Nesta fase, o trabalho principal é consolidar, documentar e refinar o MVP sem abrir novas features centrais.
