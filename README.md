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
- `docs/overview.md` — resumo curto de apoio sobre a fase atual do MVP.

## Como rodar

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Por padrão, o frontend espera a API em `http://127.0.0.1:8000`. Se necessário, ajuste `VITE_API_URL`.

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
