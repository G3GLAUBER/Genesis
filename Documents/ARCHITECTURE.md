# Gênesis — Arquitetura Oficial

Versão: 1.0

---

# Objetivo

O Gênesis é um Sistema Operacional de Inteligência Modular.

Seu objetivo é permitir que diferentes motores (Engines), agentes (Agents) e interfaces (Interfaces) trabalhem de forma desacoplada através de um núcleo comum.

---

# Princípios

## 1. Modularidade

Cada módulo deve possuir uma única responsabilidade.

Exemplo:

CLI
→ recebe comandos.

Doctor
→ verifica a saúde do sistema.

Memory
→ gerencia memória.

Knowledge
→ gerencia conhecimento.

---

## 2. Baixo Acoplamento

Nenhum módulo deve depender diretamente de outro.

A comunicação deve ocorrer através do:

- Orchestrator
- EventBus

---

## 3. Alta Coesão

Cada arquivo deve resolver apenas um problema.

Evitar arquivos gigantes.

---

## 4. Testabilidade

Toda funcionalidade nova deve possuir testes automatizados.

---

## 5. Evolução Incremental

Nenhuma Sprint adicionará funcionalidades sem antes estabilizar as anteriores.

---

# Camadas

Usuário

↓

CLI

↓

Orchestrator

↓

Services

↓

Engines

↓

Storage

---

# Estrutura

Core/

Responsável por:

- EventBus
- Dispatcher
- Registry
- Lifecycle
- Orchestrator

---

CLI/

Responsável por:

- receber comandos
- validar argumentos
- encaminhar para o módulo correto

Nunca conter lógica de negócio.

---

Engines/

Motores internos.

Exemplo:

Memory

Knowledge

Search

AI Router

---

Services/

Camada de regras de negócio.

---

Agents/

Agentes inteligentes.

Nunca acessam Storage diretamente.

---

Storage/

Persistência.

Arquivos.

Banco.

Vetores.

---

# Fluxo Oficial

Blueprint

↓

Código

↓

Teste

↓

Review

↓

Commit

↓

Push

---

# Regra Principal

Se uma funcionalidade não puder ser explicada em poucas frases, ela está grande demais e deve ser dividida.
