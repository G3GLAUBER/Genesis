#!/usr/bin/env python3

import sys
from uuid import uuid4

from CLI.doctor import run_doctor
from Core.configuration import Configuration
from Core.context import Context
from Core.Orchestrator.orchestrator import Orchestrator
from Core.registry import Registry
from Core.result import Result


def banner(config: Configuration) -> None:
    print("=" * 50)
    print(f"                 {config.system_name.upper()}")
    print("=" * 50)
    print("Sistema Operacional de Inteligência")
    print(f"Versão: {config.version}")
    print(f"Ambiente: {config.environment}")
    print("=" * 50)


def doctor() -> Result:
    return run_doctor()


def memory() -> None:
    print("Abrindo Memory Engine...")


def help_menu() -> None:
    print("\nComandos disponíveis:\n")
    print("doctor")
    print("memory")
    print("help")


def main() -> None:
    config = Configuration.default()
    banner(config)

    registry = Registry()
    orchestrator = Orchestrator(registry)

    orchestrator.register("doctor", doctor)
    orchestrator.register("memory", memory)
    orchestrator.register("help", help_menu)

    if len(sys.argv) == 1:
        help_menu()
        return

    command = sys.argv[1].lower()

    context = Context.create(
        session_id=str(uuid4()),
        command=command,
        source="CLI",
    )

    try:
        result = orchestrator.dispatch(context)

        if isinstance(result, Result):
            sys.exit(0 if result.is_success else 1)

        if isinstance(result, int):
            sys.exit(result)
    except ValueError as error:
        print(f"\n{error}")
        help_menu()
        sys.exit(2)


if __name__ == "__main__":
    main()
