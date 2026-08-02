# Blueprint — Genesis Lifecycle

**Versão:** 2.0

## Objetivo

Controlar o ciclo de vida do Kernel do Gênesis.

---

## Estados

- BOOT
- INITIALIZING
- READY
- RUNNING
- STOPPING
- STOPPED
- ERROR

---

## Responsabilidades

- armazenar o estado atual;
- permitir somente transições de estado válidas;
- consultar o estado atual;
- impedir transições inválidas;
- impedir alteração externa direta do estado;
- permitir transição para `ERROR` a partir de qualquer estado.

---

## Transições válidas

```text
BOOT → INITIALIZING
INITIALIZING → READY
READY → RUNNING
RUNNING → STOPPING
STOPPING → STOPPED
Qualquer estado → ERROR
```

Toda outra transição é inválida e deve gerar `ValueError` com os estados
de origem e destino. Uma transição inválida não altera o estado atual.

O estado é informado por `lifecycle.state`, mas não pode ser atribuído
diretamente depois da criação. Toda alteração deve ocorrer pelos métodos
públicos do Lifecycle.

---

## Interface

```python
lifecycle.state

lifecycle.initialize()

lifecycle.ready()

lifecycle.start()

lifecycle.stop()

lifecycle.stopped()

lifecycle.fail()
```

Os métodos não recebem argumentos e retornam `None` quando a transição é
concluída. `fail()` é válido em todos os estados, inclusive `ERROR`.

---

## Critérios

- [x] Lifecycle criado
- [x] Estados implementados
- [x] Transições válidas implementadas
- [x] Transições inválidas protegidas
- [x] Estado externo somente para leitura
- [x] Testes automatizados
