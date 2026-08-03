# AGENTS.md — Guia para agentes de código

Este arquivo define as regras de trabalho para qualquer agente de código que atue no repositório Genesis.

## Autoridade documental

Antes de modificar o projeto, leia nesta ordem:

1. `Documents/GenesisConstitution.md` — Constituição canônica;
2. `Documents/ADR/*.md` — decisões arquiteturais aceitas e vigentes;
3. `Documents/ARCHITECTURE.md` — arquitetura oficial e estado atual;
4. `Documents/ROADMAP.md` — sequência de evolução planejada;
5. todos os Blueprints aplicáveis em `Blueprints/`;
6. o código relacionado à mudança;
7. os testes relacionados e consumidores dos contratos afetados.

A precedência normativa é: Constituição → ADRs vigentes → Architecture →
Roadmap → Blueprints → código → testes. Código e testes comprovam o estado
implementado, mas não tornam válida uma violação de documento superior.

Em caso de conflito, não escolha silenciosamente uma interpretação e não amplie
o escopo da mudança. Registre o conflito, aplique o documento vigente de maior
autoridade e corrija primeiro a fonte inferior por Blueprint ou review
arquitetural quando necessário. Documentos marcados como `Superseded`,
`Archived` ou históricos não são normativos. A política completa e os caminhos
canônicos estão em `Documents/ADR/ADR-002-Documentation-Authority.md`.

## Missão e visão

O Gênesis é um Sistema Operacional de Inteligência Modular: uma plataforma para que Engines, Agents e Interfaces trabalhem de forma desacoplada por meio de um núcleo comum. A missão é oferecer uma fundação simples, sólida, testável e extensível para coordenar capacidades de inteligência sem prender o sistema a um fornecedor, motor ou interface específica.

A integridade da arquitetura tem prioridade sobre a velocidade. O projeto evolui incrementalmente: estabilize a fundação existente antes de acrescentar novas capacidades, mantenha responsabilidades coesas e preserve uma única fonte oficial de verdade para cada responsabilidade.

## Arquitetura atual

O fluxo implementado atualmente é:

```text
Usuário
  ↓
CLI
  ↓
Context → Orchestrator → Registry → handler/módulo
  ↓
Result ou resposta
```

A comunicação desacoplada entre componentes também pode seguir:

```text
Event → EventBus → Dispatcher → listeners
```

Componentes existentes do Core:

- `configuration.py`: configurações centrais e valores padrão imutáveis.
- `context.py`: contexto imutável de uma execução.
- `result.py`: retorno padronizado e imutável de sucesso ou erro.
- `registry.py`: registro e descoberta de módulos/handlers.
- `Core/Orchestrator/orchestrator.py`: coordenação e despacho de comandos, sem regras de negócio.
- `events.py`, `event_bus.py` e `dispatcher.py`: eventos e comunicação desacoplada; a falha de um listener não interrompe os demais.
- `logger.py`: interface central de logs.
- `lifecycle.py`: estados e ciclo de vida do Kernel.

`Services/` e `Storage/` são conceitos planejados, não camadas implementadas nem
aprovadas para uso. Não simule sua existência nem antecipe abstrações sem
Blueprint e review arquitetural. `Core/Orchestrator/router.py` e
`Core/Orchestrator/session.py` estão vazios. `Engines/` contém componentes
funcionais de AI, Mission, Planning, Execution e Workspace, além de estruturas
vazias ou experimentais. `Application/` coordena casos de uso e a composição
das dependências para Interfaces. `Agents/` permanece inicial.

## Responsabilidades por área

### CLI

`CLI/` é o ponto único de entrada. Recebe comandos, valida argumentos, cria o `Context`, encaminha a solicitação ao Orchestrator e apresenta respostas amigáveis. O Doctor audita a saúde do projeto e não corrige arquivos, instala dependências, altera código ou executa commits. A CLI e outras Interfaces nunca devem conter regras de negócio.

### Core

`Core/` é o Kernel compartilhado. Mantém contratos e infraestrutura de coordenação: Configuration, Context, Result, Registry, Orchestrator, EventBus, Dispatcher, Logger e Lifecycle. O Core deve permanecer pequeno, coeso e estável; nunca depende de Engines e não conhece detalhes internos de módulos ou fornecedores.

### Application

`Application/` coordena casos de uso entre Interfaces e Engines e centraliza a
composição das dependências. Não contém regras de domínio, persistência ou
estado global. Interfaces devem reutilizar seus serviços em vez de compor Engines
diretamente.

### Engines

`Engines/` abriga motores internos especializados, como Memory, Knowledge, Search ou AI Router. Engines implementam capacidades atrás de contratos estáveis e se comunicam por Orchestrator/EventBus, sem introduzir dependências no sentido inverso para o Core.

### Agents

`Agents/` abriga agentes inteligentes que compõem capacidades do sistema. Agents usam os contratos e fluxos oficiais, não acessam Storage diretamente e não devem acoplar o Kernel a SDKs ou APIs de provedores.

### Tests

`Tests/` protege contratos, comportamento e compatibilidade. Todo componente ou comportamento novo exige testes automatizados; correções devem incluir teste de regressão quando aplicável. Mantenha os testes determinísticos, isolados e alinhados aos Blueprints. Arquivos de teste usam `test_<componente>.py` e funções usam `test_<comportamento>()`.

## Independência de provedores de IA

O Kernel deve ser independente de qualquer fornecedor de IA. É proibido importar SDKs de provedores, usar modelos específicos ou incorporar credenciais e detalhes de API em `Core/`, CLI, Interfaces ou contratos de domínio. Integrações com provedores devem ficar atrás de abstrações/adapters próprios nas camadas apropriadas, idealmente por um Engine/AI Router, e devem ser substituíveis sem alterar o Core ou seus consumidores. Nunca registre segredos no código, nos testes, nos logs ou no Git.

## Fluxo obrigatório de desenvolvimento

Toda mudança segue este fluxo, sem pular etapas:

```text
Blueprint → implementação → testes → review → commit
```

1. Localize e leia o Blueprint aplicável. Todo novo componente do Core exige Blueprint aprovado antes da implementação.
2. Inspecione a implementação, contratos e testes existentes. Reutilize ou estenda componentes existentes antes de criar novos arquivos, classes ou abstrações.
3. Implemente a menor mudança coesa capaz de atender ao Blueprint.
4. Adicione ou atualize testes automatizados e execute a suíte completa.
5. Revise o diff quanto a arquitetura, compatibilidade, simplicidade, segurança e escopo.
6. Execute o Genesis Doctor ao encerrar uma Sprint ou mudança equivalente.
7. Faça commit somente após autorização explícita do usuário. Push também exige autorização explícita e separada quando não estiver claramente incluído no pedido.

Não faça commit nem push por iniciativa própria.

## Compatibilidade e evolução

- Preserve interfaces públicas, assinaturas, formatos de `Context`, `Result`, eventos, comandos CLI e comportamentos cobertos por testes.
- Antes de alterar um contrato, identifique consumidores e riscos de regressão. Prefira evolução aditiva e migração gradual.
- Não remova, renomeie ou mude semântica existente sem necessidade explícita, justificativa e testes.
- Reutilize `Configuration`, `Context`, `Result`, `Registry`, `Orchestrator`, `EventBus`, `Dispatcher`, `Logger` e `Lifecycle` antes de criar soluções paralelas.
- Mantenha baixo acoplamento: componentes se coordenam pelo Orchestrator e EventBus; evite dependências diretas entre módulos.
- Cada módulo e arquivo deve ter uma responsabilidade clara. Se uma funcionalidade não puder ser explicada em poucas frases, divida-a.
- Não altere a arquitetura sem apresentar previamente a motivação, alternativas consideradas, impacto, riscos de compatibilidade e plano de testes. Mudanças arquiteturais exigem review antes da implementação.

## Convenções Python e nomes

- Use Python 3.12 ou superior e código compatível com a versão mínima definida em `Configuration`.
- Siga PEP 8: quatro espaços, imports no topo e linhas legíveis; prefira código simples e explícito.
- Use type hints nas interfaces novas ou modificadas e `from __future__ import annotations` quando ajudar a manter as anotações claras.
- Use `snake_case` para módulos, arquivos Python, funções, métodos e variáveis; `PascalCase` para classes e enums; `UPPER_SNAKE_CASE` para constantes.
- Preserve os nomes de diretórios de domínio existentes em `PascalCase` (`Core`, `CLI`, `Engines`, `Agents`, `Tests`, `Blueprints`, `Documents`).
- Nomeie Blueprints como `Genesis<Componente>.md` e escreva um antes de criar qualquer componente novo do Core.
- Nomeie testes como `Tests/test_<componente>.py`; cada teste deve descrever um comportamento observável.
- Prefira `pathlib.Path`, dataclasses imutáveis para objetos de valor e retornos padronizados com `Result` quando apropriado.
- Não deixe lógica com efeitos colaterais no momento do import; coloque entradas executáveis atrás de funções e de `if __name__ == "__main__":`.

## Verificação oficial

Na raiz do repositório, execute toda a suíte com:

```bash
.venv/bin/python -m pytest Tests
```

Ao final de uma Sprint, execute também:

```bash
.venv/bin/python -m CLI.main doctor
```

O Doctor é uma auditoria adicional e não substitui a suíte de testes. Se um comando não puder ser executado, informe claramente o motivo; nunca declare testes aprovados sem tê-los executado.

## Entrega de cada tarefa

Ao concluir qualquer tarefa, apresente obrigatoriamente:

- resumo objetivo do que foi alterado;
- riscos, limitações e decisões relevantes;
- testes e verificações executados, com o resultado de cada comando;
- itens não executados ou pendentes e o motivo.

Mantenha a mudança restrita ao pedido, preserve alterações preexistentes do usuário e nunca modifique arquivos alheios à tarefa.
