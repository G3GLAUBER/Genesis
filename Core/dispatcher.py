class Dispatcher:

    def dispatch(self, callbacks, event):

        for callback in callbacks:

            try:

                callback(event)

            except Exception as error:

                print(f"[Dispatcher] Erro em {callback.__name__}")

                print(error)