from database import Database


class MemoryEngine:

    def __init__(self):
        self.database = Database()
        self.memories = self.database.load()

    def add(self, text):
        self.memories.append(text)
        self.database.save(self.memories)

    def list(self):
        return self.memories


def main():
    memory = MemoryEngine()

    memory.add("Primeira memória do Projeto Gênesis")
    memory.add("Arquitetura iniciada")

    print(memory.list())


if __name__ == "__main__":
    main()    