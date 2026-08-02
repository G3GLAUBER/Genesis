# Blueprint — Genesis Lifecycle

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
- permitir transições de estado;
- consultar o estado atual;
- impedir estados inválidos.

---

## Interface

```python
lifecycle.state

lifecycle.start()

lifecycle.ready()

lifecycle.stop()

lifecycle.fail()
```

---

## Critérios

- [ ] Lifecycle criado
- [ ] Estados implementados
- [ ] Testes
- [ ] Integração
