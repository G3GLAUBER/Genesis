# Blueprint — Genesis Doctor v2

**Versão:** 2.0
**Sprint:** 7

---

# Objetivo

Transformar o Genesis Doctor em um auditor oficial da qualidade do projeto.

O Doctor deixa de verificar apenas se o projeto executa e passa a verificar também se ele está saudável do ponto de vista de engenharia.

---

# Responsabilidades

O Doctor deverá:

- Verificar versão do Python
- Verificar estrutura do projeto
- Verificar arquivos essenciais
- Verificar Blueprints obrigatórios
- Verificar estado do Git
- Verificar quantidade de testes
- Calcular um Health Score

---

# Health Score

Cada categoria aprovada adiciona pontos.

| Item | Peso |
|------|-----:|
| Python | 15 |
| Estrutura | 15 |
| Arquivos | 15 |
| Blueprints | 15 |
| Git | 20 |
| Testes | 20 |

Total:

100 pontos

---

# Resultado

### 100

Sistema saudável.

### 80–99

Bom.

### 60–79

Atenção.

### abaixo de 60

Crítico.

---

# Fora do escopo

O Doctor NÃO deve:

- corrigir problemas;
- alterar arquivos;
- executar commits;
- modificar código;
- instalar dependências.

Sua função é apenas auditar e informar.

---

# Arquitetura

Genesis Doctor

↓

Checks independentes

↓

Resultado consolidado

↓

Health Score

↓

Relatório

---

# Critérios de conclusão

- [x] Blueprint aprovado
- [x] Doctor v2 implementado
- [x] Health Score funcionando
- [x] Git Status validado
- [x] Blueprints validados
- [x] Testes contabilizados
- [x] Testes automatizados
