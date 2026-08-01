#!/usr/bin/env python3

import sys
from uuid import uuid4

from CLI.doctor import run_doctor
from Core.configuration import Configuration
from Core.context import Context
from Core.Orchestrator.orchestrator import Orchestrator
from Core.registry import Registry


def banner(config: Configuration):
    print("=" * 50)
    print(f"                 {config.system_name.upper()}")
    print("=" * 50)
    print("Sistema Operacional de Inteligência")
    print(f"Versão: {config.version}")
    print(f"Ambiente: {config.environment}")
    print("=" * 50)


def doctor():
    return run_doctor()


def memory():
    print("Abrindo Memory Engine...")


def help_menu():
    print("\nComandos disponíveis:\n")
    print("doctor")
    print("memory")
    print("help")


def main():
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

        if isinstance(result, int):
            sys.exit(result)
    except ValueError as error:
        print(f"\n{error}")
        help_menu()


if __name__ == "__main__":
    main()
