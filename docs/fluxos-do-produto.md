# Fluxos do produto

## 1. Fluxo de descoberta e sugestão

**Ponto de entrada**
- Home.

**Ação principal do usuário**
- observar os livros em destaque e abrir um livro para decidir seu lugar no percurso.

**Resposta do sistema**
- a API entrega sugestões divididas entre `featured`, candidatos vindos da shortlist e fallback;
- o sistema considera memória mínima de percurso para não repetir foco de forma cega.

**Estado resultante**
- a pessoa identifica um próximo livro possível e pode seguir para a página do livro.

## 2. Fluxo de shortlist

**Ponto de entrada**
- Página do livro.

**Ação principal do usuário**
- marcar o livro como `shortlist`.

**Resposta do sistema**
- o backend atualiza `reading_state`;
- a home e os snapshots seguintes passam a tratar esse livro como guardado para depois.

**Estado resultante**
- o livro sai do estado neutro e passa a compor a shortlist.

## 3. Fluxo de início de leitura

**Ponto de entrada**
- Página do livro.

**Ação principal do usuário**
- marcar o livro como `current`.

**Resposta do sistema**
- o backend grava o novo estado do livro;
- o frontend atualiza leitura atual, home, sugestões e demais snapshots relacionados.

**Estado resultante**
- existe um livro em leitura atual e a tela de leitura passa a ser o centro do percurso.

## 4. Fluxo de sessão de leitura

**Ponto de entrada**
- Tela `Leitura atual`.

**Ação principal do usuário**
- registrar até onde leu, como a leitura foi sentida e uma nota opcional.

**Resposta do sistema**
- a API cria uma linha em `reading_sessions`;
- o sistema recompõe a sessão mais recente, o histórico recente e a trajetória da leitura.

**Estado resultante**
- a leitura passa a ter memória concreta de avanço.

## 5. Fluxo de reflexão

**Ponto de entrada**
- Bloco de mediação curta na tela `Leitura atual`.

**Ação principal do usuário**
- responder as perguntas breves sugeridas para a sessão mais recente.

**Resposta do sistema**
- a API grava as respostas em `reading_reflections`;
- o sistema entende que aquela sessão já recebeu sua camada breve de reflexão.

**Estado resultante**
- a sessão passa a ter registro reflexivo mínimo.

## 6. Fluxo de devolutiva

**Ponto de entrada**
- Após salvar a reflexão da sessão mais recente.

**Ação principal do usuário**
- concluir o envio da reflexão.

**Resposta do sistema**
- a API gera uma devolutiva curta e a persiste em `reading_feedback`;
- o frontend mostra esse retorno como eco breve da leitura.

**Estado resultante**
- a sessão mais recente passa a carregar uma devolutiva mínima associada.

## 7. Fluxo de trajetória

**Ponto de entrada**
- Home e tela `Leitura atual`.

**Ação principal do usuário**
- seguir registrando sessões ao longo do tempo.

**Resposta do sistema**
- o backend recalcula, a partir das sessões do livro atual, um retrato de trajetória com contagem, feeling dominante e texto breve.

**Estado resultante**
- o produto passa a exibir uma memória mais legível do caminho daquela leitura.

## 8. Fluxo de conclusão

**Ponto de entrada**
- Tela `Leitura atual`.

**Ação principal do usuário**
- acionar `Concluir leitura`.

**Resposta do sistema**
- o backend remove o livro de `current`, marca o estado como `completed` e preserva o histórico anterior;
- o frontend navega para a tela de concluídos com uma mensagem de confirmação.

**Estado resultante**
- a leitura ativa se encerra e o livro entra em `Concluídos` com memória breve de fechamento.

## 9. Fluxo de passagem para o próximo livro

**Ponto de entrada**
- Home ou tela `Concluídos`, após uma conclusão.

**Ação principal do usuário**
- voltar a explorar o catálogo e escolher o próximo foco.

**Resposta do sistema**
- as sugestões deixam de priorizar o livro recém-concluído como destaque imediato;
- shortlist e catálogo disponível reassumem o papel de próximos caminhos.

**Estado resultante**
- o produto reabre o ciclo sem apagar o percurso anterior.
