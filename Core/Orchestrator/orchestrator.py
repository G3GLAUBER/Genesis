class Orchestrator:
    """
    Núcleo de coordenação do Projeto Gênesis.

    Recebe comandos e os encaminha para o módulo responsável.
    """

    def __init__(self):
        self._routes = {}

    def register(self, command, handler):
        """
        Registra um comando.
        """
        self._routes[command] = handler

    def dispatch(self, command, *args, **kwargs):
        """
        Encaminha um comando para o módulo responsável.
        """

        if command not in self._routes:
            raise ValueError(f"Comando desconhecido: {command}")

        return self._routes[command](*args, **kwargs)
