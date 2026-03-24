# Runbook local

## Pré-requisitos

- Python 3.11+ disponível no ambiente local;
- Node.js 20+ com `npm`;
- portas locais `8000` e `5173` livres, de preferência;
- terminal com suporte a variáveis de ambiente simples.

## Comandos para backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verificação rápida:

```bash
curl http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok"}
```

## Comandos para frontend

```bash
cd frontend
npm install
export VITE_API_URL=http://127.0.0.1:8000
npm run dev -- --host 127.0.0.1 --port 5173
```

## Observações sobre portas

- backend sugerido: `127.0.0.1:8000`;
- frontend sugerido: `127.0.0.1:5173`;
- o backend já aceita CORS para `http://localhost:5173` e `http://127.0.0.1:5173`;
- se o backend subir em outra porta, `VITE_API_URL` deve apontar exatamente para ela.

## Fluxo mínimo de operação local

1. iniciar o backend;
2. validar `GET /health`;
3. iniciar o frontend com `VITE_API_URL` correto;
4. abrir a home;
5. escolher um livro e definir `current` ou `shortlist`;
6. registrar uma sessão na leitura atual;
7. responder a reflexão, quando houver;
8. observar devolutiva, trajetória e concluídos;
9. concluir a leitura atual e retornar à home.

## Resolução curta de problemas comuns

Os cenários operacionais tratados abaixo são: porta ocupada, frontend fora do ar, backend fora do ar e API apontando para porta errada.

### Porta ocupada

Sintoma: backend ou frontend falha ao iniciar informando que a porta já está em uso.

Ação:
- subir o processo em outra porta disponível;
- se mudar a porta do backend, atualizar `VITE_API_URL` antes de subir o frontend.

### Frontend fora do ar

Sintoma: a interface não abre em `127.0.0.1:5173`.

Ação:
- verificar se `npm install` foi executado;
- conferir se o comando `npm run dev -- --host 127.0.0.1 --port 5173` está ativo;
- revisar mensagens do terminal do Vite.

### Backend fora do ar

Sintoma: `curl http://127.0.0.1:8000/health` falha ou a interface mostra erros de carregamento.

Ação:
- confirmar se o ambiente virtual foi ativado;
- confirmar se `pip install -r requirements.txt` foi executado;
- reiniciar `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.

### API apontando para porta errada

Sintoma: frontend abre, mas não carrega catálogo, sugestões ou snapshots.

Ação:
- verificar o valor de `VITE_API_URL` no terminal em que o frontend foi iniciado;
- conferir se o endereço bate com a porta real do backend;
- reiniciar o frontend após corrigir a variável.
