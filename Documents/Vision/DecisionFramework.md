# Genesis Decision Framework

**Versão:** 1.0  
**Status:** framework obrigatório para novas decisões de produto

## Regra fundamental

Toda nova funcionalidade, experiência, Copilot, Plugin, Agent, integração ou
destino deve responder:

1. **Ajuda o usuário a decidir melhor?**
2. **Ajuda o usuário a executar melhor?**
3. **Ajuda o usuário a lembrar melhor?**
4. **Ajuda o usuário a progredir continuamente?**

> **Se todas as respostas forem NÃO, a proposta deve ser rejeitada.**

Uma resposta “sim” não garante aprovação. Apenas prova que a proposta pode
pertencer ao problema Genesis.

## Stage 1 — Progress Fit

### Decidir melhor

Considerar SIM quando a proposta melhora contexto, critérios, comparação,
Confidence, percepção de Risk ou compreensão de consequência.

Não conta:

- produzir mais opções sem recomendação;
- gerar conteúdo que não altera julgamento;
- apresentar métricas sem decisão associada.

### Executar melhor

Considerar SIM quando a proposta reduz trabalho sem valor, melhora qualidade,
coordena Handoffs, preserva controle ou aproxima um resultado verificável.

Não conta:

- automatizar atividade sem outcome;
- acelerar uma ação errada;
- remover supervisão onde há consequência material.

### Lembrar melhor

Considerar SIM quando a proposta preserva origem, decisão, preferência,
aprendizado ou contexto que melhora trabalho futuro.

Não conta:

- acumular dados sem propósito;
- esconder Memory do usuário;
- guardar atividade apenas porque existe.

### Progredir continuamente

Considerar SIM quando a proposta liga o momento atual ao próximo Progress Event
e mantém continuidade até ao resultado.

Não conta:

- aumentar engagement;
- criar um destino sem jornada;
- terminar numa resposta sem próxima ação.

## Stage 2 — Genesis Fit

Uma proposta que passa Progress Fit deve responder:

1. Por que pertence ao Genesis?
2. Em que ponto do ciclo Compreender, Propor, Decidir, Agir, Rever e Lembrar
   entra?
3. Qual conceito oficial representa a proposta?
4. Pode aprofundar um espaço existente em vez de criar outro?
5. Mantém uma relação única com Genesis?
6. Usa o Product Vocabulary sem termos conflitantes?
7. Continua coerente num horizonte de cinco anos?

Rejeitar quando a proposta:

- transforma Genesis em ERP, Dashboard administrativo ou chatbot;
- existe para expor tecnologia;
- duplica responsabilidade;
- exige que o usuário opere providers;
- cria personalidade ou produto paralelo;
- adiciona complexidade maior que o valor.

## Stage 3 — Trust Fit

Toda proposta aprovada em princípio precisa demonstrar:

- contexto utilizado e origem compreensíveis;
- Confidence proporcional à evidência;
- Risk visível antes da consequência;
- consentimento explícito quando necessário;
- possibilidade de Review, Pause, Stop ou Undo;
- comportamento seguro em falha parcial;
- trabalho e entradas preservados;
- Memory governável;
- acessibilidade desde o início;
- privacidade e fronteiras de Workspace respeitadas.

Se Trust Fit falhar, a proposta não avança, ainda que gere progresso.

## Stage 4 — Simplicity Fit

Perguntas obrigatórias:

1. O que será removido ou combinado?
2. Quantos novos conceitos são necessários?
3. Existe uma única ação principal?
4. A pessoa compreende sem formação?
5. Funciona com cinco vezes mais Projects ou pessoas?
6. A navegação permanece estável?
7. O estado vazio ensina valor?
8. Erro e recuperação são mais simples do que o happy path permite supor?

Subtração é uma entrega. Uma proposta pode ser aprovada para remover ou
simplificar mesmo sem adicionar capacidade.

## Stage 5 — Business Fit

Uma proposta deve declarar:

- cliente e problema prioritários;
- evidência disponível;
- outcome esperado;
- impacto em Progress Continuity Rate;
- valor económico ou estratégico;
- custo de oportunidade;
- guardrails;
- condição de interrupção;
- plano de aprendizagem;
- relação com a fase atual do Product Roadmap.

Receita potencial não supera conflito com North Star, Trust ou identidade.

## Stage 6 — Foundation and Authority Fit

Antes de seguir, verificar:

- compatibilidade com fontes canônicas superiores;
- necessidade de review de arquitetura;
- existência da fundação exigida;
- impacto em contratos e consumidores;
- fase correta no Roadmap;
- decisão formal do Product Council.

Uma proposta valiosa pode receber **Hold** quando a fundação ainda não existe.
Hold protege sequência; não invalida o problema.

## Scorecard

| Dimensão | Pergunta | Resultado |
|---|---|---|
| Progress | Melhora decidir, executar, lembrar ou progredir? | Sim/Não |
| Identity | Parece inequivocamente Genesis? | Pass/Revise |
| Trust | Preserva contexto, consentimento e controle? | Pass/Block |
| Simplicity | Reduz ou contém complexidade? | Pass/Revise |
| Business | Há cliente, valor e evidência? | Pass/Hold |
| Authority | Respeita decisões e sequência vigentes? | Pass/Hold |

O scorecard não produz média. Um **Block** em Trust ou conflito de Authority
impede aprovação.

## Resultados

### Approve

Direção coerente, evidência suficiente e próxima etapa clara.

### Approve with conditions

Direção correta, condicionada a guardrails verificáveis.

### Revise

Problema válido; solução precisa simplificação ou reenquadramento.

### Hold

Problema válido; evidência, fundação ou fase ainda insuficiente.

### Reject

Não melhora nenhum dos quatro resultados centrais, viola identidade ou cria
risco inaceitável.

## Decision brief obrigatório

Toda proposta ao Product Council contém:

1. decisão necessária;
2. problema do cliente;
3. evidência e assumptions;
4. respostas às quatro perguntas fundamentais;
5. Recommendation;
6. alternativas consideradas;
7. jornada e próxima ação;
8. Trust e Accessibility;
9. impacto em simplicidade;
10. Success Metric e guardrails;
11. fase do Roadmap;
12. incertezas abertas.

## Teste final

Antes de aprovar, completar a frase:

> Esta decisão ajuda **[cliente]** a **[decidir, executar, lembrar ou
> progredir]** melhor porque **[mecanismo de valor]**, preservando **[controle e
> guardrails]**, e saberemos que funcionou quando **[resultado mensurável]**.

Se a frase depender de “mais engagement”, “mais uso de IA” ou “mais conteúdo”,
a proposta ainda não demonstra valor Genesis.
