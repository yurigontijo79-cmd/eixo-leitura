# MVP canônico — EIXO Leitura

## O que é o EIXO Leitura

O EIXO Leitura é um produto de leitura guiada focado em ajudar a pessoa a escolher um livro, iniciar a leitura com intenção, registrar sessões curtas e manter uma memória discreta do percurso.

Seu núcleo não está em entregar conteúdo, mas em organizar a relação entre escolha, continuidade, reflexão breve e encerramento de uma leitura.

## O que ele não é

O EIXO Leitura não é:

- não é leitor de ebook;
- não é loja de livros;
- não é dashboard de produtividade;
- não é app gamificado.

Também não foi desenhado, nesta fase, para ser uma plataforma social, um sistema de analytics pesados ou um produto centrado em meta, ranking e desempenho.

## Qual problema ele resolve

O MVP resolve um problema simples e específico: muitas leituras começam sem intenção, se perdem no meio do caminho e terminam sem memória do que aconteceu.

O produto organiza esse percurso com mediação mínima. Em vez de cobrar performance, ele ajuda a:

- decidir por onde começar;
- guardar livros que ainda não são prioridade;
- registrar onde a leitura parou e como ela foi sentida;
- produzir uma reflexão curta quando faz sentido;
- devolver uma síntese breve do momento da leitura;
- preservar uma memória do livro quando o percurso se encerra.

## Identidade central do produto

A identidade do EIXO Leitura é a de um mediador discreto de percurso.

Isso significa que o produto:

- trabalha com poucos estados e poucos fluxos;
- mantém linguagem curta e sóbria;
- usa regras determinísticas em vez de complexidade excessiva;
- valoriza continuidade e memória, não volume de interação;
- privilegia clareza de uso sobre ambição estrutural.

## O que faz parte do MVP canônico

O núcleo oficial do MVP cobre:

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

Na prática, isso significa que o produto já permite:

1. escolher um livro a partir de sugestões simples;
2. mover livros entre foco atual, shortlist e fora de prioridade;
3. registrar sessões curtas da leitura atual;
4. responder perguntas breves associadas à sessão mais recente;
5. gerar um retorno textual curto ligado ao momento da leitura;
6. exibir um retrato resumido da trajetória do livro atual;
7. concluir uma leitura e manter sua memória em concluídos;
8. voltar ao catálogo com espaço para o próximo começo.

## O que foi deliberadamente deixado de fora nesta fase

Para preservar a forma do MVP, ficaram fora do escopo canônico:

- leitura de ebook dentro do produto;
- compra de livros;
- cadastro multiusuário e autenticação;
- recomendação semântica complexa;
- IA pesada ou geração aberta em larga escala;
- dashboards de performance;
- gamificação, ranking, streaks e recompensas;
- camadas sociais, comentários ou comunidade;
- curadoria editorial complexa com backoffice próprio;
- automações estruturais que abram nova frente de produto.

Esses pontos não estão “faltando”. Eles foram conscientemente adiados ou vetados para que o MVP permaneça legível, testável e fiel à sua proposta.

## Estado oficial atual do MVP

O estado oficial atual do MVP é: funcional, coerente e fechado em seu núcleo.

O produto já possui:

- backend com persistência em SQLite;
- API com rotas para catálogo, estado de leitura, sessões, reflexões, devolutiva, trajetória, sugestões e concluídos;
- frontend navegável com as telas centrais do percurso;
- regras determinísticas para sugestões, perguntas, devolutivas, trajetória e encerramento;
- lapidação mínima de UX e microtexto suficiente para sustentar a identidade do produto.

## Posição canônica desta fase

Esta documentação congela o MVP como base canônica do EIXO Leitura.

O trabalho seguinte não deve reinventar o núcleo. Deve apenas:

- esclarecer o que já existe;
- refinar o que já foi validado;
- ampliar com cautela aquilo que não descaracteriza o produto.
