# Arquitetura do MVP

## Stack do MVP

O MVP canônico usa:

- React;
- Vite;
- TypeScript;
- FastAPI;
- SQLite.

A arquitetura foi mantida simples de propósito: uma SPA no frontend, uma API HTTP única no backend e um banco local com poucas tabelas centrais.

## Visão geral do frontend

O frontend é uma aplicação React com roteamento por página e um contexto central de dados.

Estrutura lógica principal:

- `App.tsx` define as rotas principais;
- `components/AppShell.tsx` fornece a casca de navegação;
- `pages/*` implementa as telas centrais do produto;
- `context/LibraryContext.tsx` centraliza carregamento, refresh e mutações;
- `services/api.ts` concentra as chamadas HTTP;
- `types/book.ts` descreve os snapshots e entidades consumidos pela interface.

## Visão geral do backend

O backend expõe uma API FastAPI única.

Sua organização foi separada em três camadas simples:

- `api/`: rotas HTTP e contratos de entrada/saída;
- `core/`: inicialização, configuração e acesso ao banco;
- `services/`: regras do domínio para sugestões, perguntas, devolutiva, trajetória e encerramento.

A camada de banco também cumpre parte da orquestração do MVP. Isso foi aceito nesta fase para evitar abstração excessiva.

## Banco e tabelas principais

O banco é SQLite e o schema principal está em `database/schema.sql`.

Tabelas centrais:

### `books`
Persistida.

Guarda o catálogo base do MVP:

- `id`
- `title`
- `author`
- `description`

### `reading_state`
Persistida.

Guarda o estado mais recente do livro dentro do fluxo do produto:

- `book_id`
- `state` (`current`, `shortlist`, `rejected`, `completed`)
- `created_at`
- `updated_at`

### `reading_sessions`
Persistida.

Guarda cada sessão curta registrada para um livro:

- `book_id`
- `progress_text`
- `feeling`
- `note`
- `created_at`

### `reading_reflections`
Persistida.

Guarda as respostas breves associadas a uma sessão:

- `reading_session_id`
- `question_key`
- `question_text`
- `answer_text`
- `created_at`

### `reading_feedback`
Persistida.

Guarda a devolutiva mínima gerada para uma sessão:

- `reading_session_id`
- `text`
- `created_at`

## Entidades principais do domínio

As entidades e snapshots centrais do MVP são:

- `books`: catálogo base consultado pelo frontend e enriquecido com estado de leitura;
- `reading_state`: snapshot do foco atual, shortlist e contagem de rejeitados;
- `reading_sessions`: snapshot da sessão mais recente e histórico recente da leitura atual;
- `reading_reflections`: snapshot da sessão em aberto para reflexão e perguntas sugeridas;
- `reading_feedback`: devolutiva textual breve associada a uma sessão.

Outros snapshots derivados importantes:

- `completed_books`: visão consolidada dos livros já concluídos;
- `reading_trajectory`: retrato textual e metadados do percurso do livro atual;
- `suggestions`: divisão da home entre destaque principal, shortlist e fallback.

## Rotas principais da API

Rotas centrais do MVP:

- `GET /books`
- `GET /suggestions`
- `GET /reading-state`
- `POST /reading-state`
- `POST /reading-state/complete`
- `GET /reading-sessions/current`
- `POST /reading-sessions`
- `GET /reading-reflections/current`
- `POST /reading-reflections`
- `POST /reading-feedback/generate`
- `GET /reading-trajectory/current`
- `GET /completed-books`
- `GET /health`

## Responsabilidades por camada

### Frontend

Responsável por:

- navegação entre as telas centrais;
- exibição do estado atual do percurso;
- envio de ações do usuário para a API;
- apresentação de microtextos, estados vazios e erros;
- composição dos snapshots recebidos do backend.

### Backend HTTP

Responsável por:

- validar payloads e contratos;
- expor snapshots consumíveis pela interface;
- coordenar mutações do estado de leitura;
- devolver respostas estáveis e simples.

### Regras de domínio

Responsáveis por:

- ordenar sugestões;
- escolher perguntas de reflexão;
- variar devolutivas mínimas;
- inferir a trajetória da leitura;
- montar o texto breve de encerramento.

### Persistência

Responsável por:

- manter catálogo, estados, sessões, reflexões e devolutivas;
- recompor snapshots lidos pelo frontend;
- sustentar o histórico mínimo necessário para o MVP.

## Principais estados do livro

Os estados centrais do livro no produto são:

- `current`: livro em leitura agora;
- `shortlist`: livro guardado para depois;
- `rejected`: livro tirado do foco nesta fase;
- `completed`: livro concluído e preservado em memória.

No frontend, o catálogo também admite `state: null`, usado quando o livro existe no catálogo, mas ainda não recebeu um estado ativo no percurso.

## O que é persistido

É persistido no banco:

- catálogo base (`books`);
- estados de leitura (`reading_state`);
- sessões (`reading_sessions`);
- reflexões (`reading_reflections`);
- devolutivas (`reading_feedback`).

## O que é derivado

É derivado a partir dos dados persistidos:

- sugestões da home;
- trajetória atual da leitura;
- perguntas sugeridas para reflexão;
- texto de encerramento exibido em concluídos;
- contagens e resumos agregados exibidos nos snapshots.

## O que foi mantido simples de propósito

Algumas decisões de simplificação são parte do desenho do MVP:

- banco único SQLite, sem infraestrutura distribuída;
- catálogo pequeno e sem painel de administração;
- uma única pessoa usuária implícita, sem autenticação;
- regras determinísticas em vez de motores complexos de recomendação;
- poucas telas e poucos estados principais;
- acoplamento controlado entre camada de banco e composição de snapshots, para reduzir cerimônia.
