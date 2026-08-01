#!/usr/bin/env python3

import sys

from Core.Orchestrator.orchestrator import Orchestrator
from Core.registry import Registry
from CLI.doctor import run_doctor


def banner():
    print("=" * 50)
    print("                 GÊNESIS")
    print("=" * 50)
    print("Sistema Operacional de Inteligência")
    print("Versão: 0.1")
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
    banner()

    registry = Registry()
    orchestrator = Orchestrator(registry)

    orchestrator.register("doctor", doctor)
    orchestrator.register("memory", memory)
    orchestrator.register("help", help_menu)

    if len(sys.argv) == 1:
        help_menu()
        return

    command = sys.argv[1].lower()

    try:
        exit_code = orchestrator.dispatch(command)

        if isinstance(exit_code, int):
            sys.exit(exit_code)
    except ValueError as error:
        print(f"\n{error}")
        help_menu()


if __name__ == "__main__":
    main()
