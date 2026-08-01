from Core.context import Context
from Core.registry import Registry


class Orchestrator:
    """
    Núcleo de coordenação do Projeto Gênesis.

    Recebe um Context, consulta o Registry e executa
    o módulo responsável pelo comando.
    """

    def __init__(self, registry: Registry):
        self._registry = registry

    def register(self, command, handler):
        """
        Registra um comando no Registry.
        """
        self._registry.register(command, handler)

    def dispatch(self, context: Context, *args, **kwargs):
        """
        Busca o comando presente no Context e executa
        o responsável registrado.
        """
        try:
            handler = self._registry.get(context.command)
        except ValueError as error:
            raise ValueError(
                f"Comando desconhecido: {context.command}"
            ) from error

        return handler(*args, **kwargs)
