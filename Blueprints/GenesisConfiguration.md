# Blueprint — Genesis Configuration

## Objetivo

Centralizar as configurações do Projeto Gênesis.

---

## Responsabilidades

- armazenar configurações do sistema;
- fornecer valores padrão;
- permitir leitura segura das configurações;
- evitar valores espalhados pelo código.

---

## Configurações iniciais

- nome do sistema;
- versão;
- ambiente;
- versão mínima do Python;
- pasta de dados;
- pasta de logs.

---

## Interface pública

```python
config = Configuration.default()
config.system_name
config.version
config.environment
config.minimum_python_version
config.data_directory
config.logs_directory
