# Memory experimental legado

`database.py`, `data/memory.json`, `config.py`, `exceptions.py`, `index.py`,
`indexer.py`, `search.py` e `docs/README.md` pertencem ao protótipo anterior.
Eles não integram a API oficial exportada por `Engines.Memory` e não são
carregados pelo `MemoryEngine`, pelo bootstrap ou pelo `MemoryService`.

O protótipo não foi reutilizado porque possui persistência JSON, caminhos
obsoletos, modelos mutáveis e nenhum isolamento por Workspace. `record.py` e
`memory.py` existem apenas como shims de importação para os contratos oficiais.
