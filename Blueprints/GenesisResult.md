# Blueprint — Genesis Result

## Objetivo

Padronizar o retorno dos módulos do Projeto Gênesis.

---

## Estrutura

Todo resultado terá:

- `is_success`: informa se a operação foi concluída
- `message`: mensagem legível
- `data`: dado opcional retornado pela operação

---

## Interface pública

### Sucesso

```python
Result.success(
    message="Operação concluída",
    data=None,
)
