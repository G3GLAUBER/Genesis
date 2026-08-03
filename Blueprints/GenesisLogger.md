# Blueprint — Genesis Logger

## Objetivo

Centralizar todos os logs do Projeto Gênesis.

---

## Responsabilidades

- registrar mensagens informativas;
- registrar avisos;
- registrar erros;
- padronizar a saída do sistema.

---

## Interface

```python
logger.info("Mensagem")

logger.warning("Mensagem")

logger.error("Mensagem")
```

---

## Benefícios

- Interface única
- Fácil evolução
- Compatível com arquivos
- Compatível com banco
- Compatível com observabilidade

---

## Critérios

- [x] Logger criado
- [x] info()
- [x] warning()
- [x] error()
- [x] Testes
