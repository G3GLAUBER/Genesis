# Blueprint — Genesis CLI

## Objetivo

Ser o ponto único de entrada do Gênesis.

## Comandos previstos

- doctor
- audit
- backup
- create
- memory
- knowledge
- chat
- update

## Responsabilidades

- Receber comandos
- Validar argumentos
- Encaminhar para o módulo correto
- Exibir mensagens amigáveis
- Converter resultados em códigos de saída consistentes

## Códigos de saída

A CLI deve aplicar o seguinte contrato ao resultado retornado pelo handler:

| Resultado | Código |
|---|---:|
| `Result.success` | `0` |
| `Result.error` | `1` |
| comando desconhecido | `2` |

Handlers que retornam diretamente um código inteiro continuam compatíveis.
Comandos sem retorno explícito terminam normalmente com código `0`.

O mapeamento do código de saída pertence à CLI e não altera o fluxo oficial:

```text
CLI → Context → Orchestrator → handler → Result → exit code
```

## Critérios de conclusão

- [x] CLI criada
- [ ] Parser de comandos
- [x] Help implementado
- [x] Doctor integrado
- [x] Códigos de saída implementados
- [x] Testes funcionando
- [x] Documentação atualizada
