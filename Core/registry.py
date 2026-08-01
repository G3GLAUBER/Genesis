class Registry:
    def __init__(self):
        self._modules = {}

    def register(self, name, module):
        if name in self._modules:
            raise ValueError(f"Módulo já registrado: {name}")

        self._modules[name] = module

    def get(self, name):
        if name not in self._modules:
            raise ValueError(f"Módulo não encontrado: {name}")

        return self._modules[name]

    def list(self):
        return list(self._modules.keys())
