from Core.registry import Registry


class Orchestrator:
    """
    Núcleo de coordenação do Projeto Gênesis.

    Recebe comandos, consulta o Registry e executa
    o módulo responsável.
    """

    def __init__(self, registry: Registry):
        self._registry = registry

    def register(self, command, handler):
        """
        Registra um comando no Registry.
        """
        self._registry.register(command, handler)

    def dispatch(self, command, *args, **kwargs):
        """
        Busca o comando no Registry e executa o responsável.
        """
        try:
            handler = self._registry.get(command)
        except ValueError as error:
            raise ValueError(f"Comando desconhecido: {command}") from error

        return handler(*args, **kwargs)
