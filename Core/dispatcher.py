from collections.abc import Callable, Iterable

from Core.events import Event
from Core.logger import Logger


class Dispatcher:
    """
    Responsável por executar listeners de eventos.
    """

    def __init__(self) -> None:
        self._logger = Logger()

    def dispatch(
        self,
        callbacks: Iterable[Callable[[Event], None]],
        event: Event,
    ) -> None:
        """
        Executa todos os callbacks registrados para um evento.

        A falha de um listener não interrompe os demais.
        """

        for callback in callbacks:
            try:
                callback(event)

            except Exception as error:
                callback_name = getattr(
                    callback,
                    "__name__",
                    type(callback).__name__,
                )
                self._logger.error(
                    f"Erro no listener '{callback_name}': {error}"
                )
