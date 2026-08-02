# Blueprint — Genesis Companion v0.1

## Objetivo

Oferecer uma interface web local mínima para criar uma missão, visualizar um
plano demonstrativo e acompanhar sua execução pelos Engines existentes.

## Arquitetura

O Companion pertence a `Interfaces/Companion/` e não contém regras de domínio:

```text
Browser → HTTP Server → CompanionApplication
                            ↓
MissionEngine → Planner → MissionExecutionEngine
                            ↓
                AIOrchestrator → FakeProvider
```

A interface compõe os componentes, traduz entrada HTTP em chamadas públicas e
renderiza seus resultados. Mission, Planning, Execution e AI continuam como
fontes oficiais das regras de negócio.

## Tecnologia

- Python 3.12;
- `http.server.ThreadingHTTPServer` da biblioteca padrão;
- HTML e CSS gerados no servidor;
- `urllib.parse` para formulários;
- sem dependências externas, JavaScript, banco ou autenticação.

## Fluxo público

1. `GET /` mostra nome, versão, ambiente e formulário;
2. `POST /missions` recebe `title` e `objective`;
3. `MissionEngine` cria a missão;
4. `Planner` cria três etapas demonstrativas encadeadas;
5. `MissionExecutionEngine` executa o plano;
6. a página mostra missão, plano, provider, resultados e relatório final.

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
- nenhuma persistência ou histórico entre requisições;
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
