from Core.registry import Registry


registry = Registry()

registry.register("MemoryEngine", object())
registry.register("KnowledgeEngine", object())
registry.register("Companion", object())

print("Módulos registrados:")

for module in registry.list():
    print("-", module)