# Blueprint — Genesis Companion

**Versão:** 0.2

## Objetivo

Oferecer a primeira interface operacional local do Genesis para acompanhar
Workspaces, projetos, missões, memórias, execuções, timeline e saúde da
aplicação.

## Arquitetura

O Companion pertence a `Interfaces/Companion/` e não contém regras de domínio:

```text
Browser → HTTP Server → CompanionApplication → Application Services
                                                ↓
                         MissionEngine → Planner → MissionExecutionEngine
                                                ↓
                                    AIOrchestrator → FakeProvider
```

A interface traduz entrada HTTP em chamadas públicas e renderiza seus
resultados. O bootstrap da camada Application compõe os componentes. Mission,
Planning, Execution e AI continuam como fontes oficiais das regras de negócio.

## Tecnologia

- Python 3.12;
- `http.server.ThreadingHTTPServer` da biblioteca padrão;
- HTML em template e CSS estático próprio;
- `urllib.parse` para formulários;
- sem dependências externas, JavaScript, banco ou autenticação.

## Fluxo público

1. `GET /` mostra nome, versão, ambiente e formulário;
2. `POST /missions` recebe `title` e `objective`;
3. `MissionEngine` cria a missão;
4. `Planner` cria três etapas demonstrativas encadeadas;
5. `MissionExecutionEngine` executa o plano;
6. a página mostra missão, plano, provider, resultados e relatório final.

## Navegação operacional

- `/`: dashboard, métricas, ação rápida e timeline;
- `/workspaces`: listagem, criação e seleção de Workspace;
- `/projects`: listagem e criação de projetos do Workspace ativo;
- `/missions`: criação, execução, listagem e status;
- `/memory`: registro, histórico, pesquisa e filtro por categoria;
- `/executions`: histórico local de execuções;
- `/doctor`: Application Health e disponibilidade dos serviços, preservando a
  rota sem representar o Genesis Doctor oficial;
- `/settings`: limites e configuração da instância local.

A Interface utiliza exclusivamente `WorkspaceApplicationService`,
`ProjectService`, `MissionApplicationService` e `MemoryService` por meio da fachada
`CompanionApplication`. Não chama Engines diretamente nos fluxos operacionais.

## Plano demonstrativo

As três etapas usam `text_generation` e são definidas pela composição da
aplicação, não por IA:

1. compreender o objetivo;
2. propor a primeira ação;
3. revisar o plano de ação.

Cada etapa posterior depende da conclusão da anterior.

## Interface pública

```python
application = CompanionApplication.default()
result = application.execute_mission(title=title, objective=objective)

server = create_server(host="127.0.0.1", port=8000)
server.serve_forever()
```

Inicialização oficial:

```bash
.venv/bin/python -m Interfaces.Companion.server
```

Endereço padrão: `http://127.0.0.1:8000/`.

## Segurança e limites

- acesso local por padrão;
- conteúdo enviado pelo usuário é escapado antes da renderização;
- corpo de requisição limitado;
- nenhuma credencial, provider real ou chamada externa;
- histórico volátil durante a vida da instância, sem persistência após restart;
- Application Health deriva da presença dos três Application Services e exibe
  `DISPONÍVEL` ou `DEGRADADO`; não executa nem substitui o Genesis Doctor;
- sem autenticação, concorrência de missões ou atualização em tempo real.

## Critérios de conclusão

- [x] formulário de título e objetivo;
- [x] missão e plano de três etapas visíveis;
- [x] execução real pelos Engines existentes;
- [x] FakeProvider e resultado de cada etapa visíveis;
- [x] relatório final visível;
- [x] testes da aplicação e do servidor;
- [x] servidor inicia e encerra de forma limpa;
- [x] nenhuma alteração no Core, CLI ou Engines.
- [x] sidebar e dashboard operacional responsivo;
- [x] páginas de missões, memórias e execuções;
- [x] página e métricas operacionais de projetos;
- [x] métricas e timeline por Workspace ativo;
- [x] HTML e CSS em arquivos separados;
- [x] compatibilidade das rotas e APIs anteriores.
