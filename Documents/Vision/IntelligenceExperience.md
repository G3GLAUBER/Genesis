# Intelligence Experience

## Definição

Intelligence é a experiência explicável pela qual Genesis transforma um pedido
em resultado. O usuário conversa com Genesis; fontes externas nunca se tornam
personagens da relação.

## Contrato da experiência

- **Objetivo:** tornar o raciocínio e o resultado julgáveis.
- **Problema:** respostas sem contexto, origem, confiança ou consequência.
- **Ação principal:** rever e decidir sobre o resultado.
- **Emoção:** confiança informada.
- **Próxima ação:** usar, ajustar, guardar ou recusar.

## Anatomia de uma Intelligence Session

### Pedido

A intenção do usuário em linguagem natural, preservada como foi compreendida.
Genesis confirma reformulações que possam alterar significado.

### Context found

Mostra o contexto usado em camadas:

1. Workspace;
2. Project;
3. Memory;
4. Knowledge;
5. restrições e decisões anteriores.

Cada fonte pode ser inspecionada ou removida da sessão.

### Intelligence plan

Genesis diz brevemente como pretende ajudar: comparar, sintetizar, gerar,
avaliar ou recomendar. Não expõe mecânica desnecessária.

### Recommended source

Quando relevante, mostra a fonte de inteligência recomendada com uma
justificativa humana: adequação, privacidade, custo, disponibilidade e qualidade
esperada. A marca não domina a composição.

### Alternatives

Alternativas aparecem com diferenças significativas, não como catálogo. A
recomendação continua claramente preferida.

### Result

Começa pela conclusão. Em seguida mostra evidências, assumptions, confidence,
risks e possíveis próximos passos.

## Linha de confiança

**Pedido → contexto encontrado → contexto escolhido → direção recomendada →
fonte coordenada → resultado → Review**

O usuário pode regressar a qualquer etapa sem perder o pedido original.

## Confidence

Evitar percentagens pseudoprecisas. Usar:

- **Alta:** contexto suficiente e evidência consistente;
- **Moderada:** direção útil com lacunas conhecidas;
- **Baixa:** hipótese que exige validação.

O nível sempre inclui “por quê” e “o que aumentaria a confiança”.

## Intelligence ativa

Estados oficiais de experiência:

- **Compreendendo contexto**;
- **Preparando Proposal**;
- **Aguardando você**;
- **Em Review**;
- **Concluída**;
- **Não concluída**.

Cada estado mostra o que acontece agora e se a pessoa pode Pause ou Stop.

## Resultado insuficiente

Genesis não disfarça fraqueza. Diz o que conseguiu confirmar, o que permanece
incerto e oferece uma pergunta, uma fonte alternativa ou um Handoff.

## Regra de identidade

Nunca escrever “pergunte ao GPT”, “resposta do Gemini” ou “converse com Claude”
como ação principal. A formulação correta é “Pedir ao Genesis”, com origem
discreta apenas quando afeta a decisão.
