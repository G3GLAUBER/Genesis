# Blueprint — Genesis Orchestrator

## Objetivo

O Orchestrator é o núcleo de coordenação do Projeto Gênesis.

Ele recebe comandos da CLI (ou de outras interfaces), identifica qual módulo é responsável pela execução e encaminha a solicitação.

O Orchestrator não implementa regras de negócio.

---

# Responsabilidades

- Receber comandos
- Validar se o comando existe
- Encaminhar para o módulo correto
- Tratar erros
- Retornar a resposta

---

# Não é responsabilidade do Orchestrator

- Manipular memória
- Salvar arquivos
- Executar IA
- Conhecer detalhes internos dos módulos

---

# Fluxo

Usuário

↓

CLI

↓

Orchestrator

↓

Module Router

↓

Módulo

↓

Resposta

↓

CLI

---

# Módulos iniciais

- Doctor
- Memory
- Knowledge
- Update
- Backup

---

# Interface pública

```python
dispatch(context, *args, **kwargs) -> Any
```

O método localiza o handler pelo comando presente no `Context`, executa-o com
os argumentos recebidos e retorna diretamente o valor produzido pelo handler.

O Orchestrator não encapsula automaticamente esse valor em `Result`. Um handler
pode retornar `Result` quando esse for o contrato específico do comando.

---

# Critérios de conclusão

- [x] Classe Orchestrator criada
- [x] Método dispatch()
- [x] Tratamento de comandos inexistentes
- [x] Integração com CLI
- [x] Testes automatizados
