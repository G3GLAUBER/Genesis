from Core.logger import Logger


class Dispatcher:
    """
    Responsável por executar listeners de eventos.
    """

    def __init__(self):
        self._logger = Logger()

    def dispatch(self, callbacks, event):
        """
        Executa todos os callbacks registrados para um evento.

        A falha de um listener não interrompe os demais.
        """

        for callback in callbacks:
            try:
                callback(event)

            except Exception as error:
                self._logger.error(
                    f"Erro no listener '{callback.__name__}': {error}"
                )
