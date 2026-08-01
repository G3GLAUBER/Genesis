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

dispatch(command, args)

↓

retorna

Result

---

# Critérios de conclusão

- [ ] Classe Orchestrator criada
- [ ] Método dispatch()
- [ ] Tratamento de comandos inexistentes
- [ ] Integração com CLI
- [ ] Testes automatizados
