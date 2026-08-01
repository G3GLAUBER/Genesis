from pathlib import Path
import sys


ESSENTIAL_DIRECTORIES = [
    "Core",
    "Engines",
    "CLI",
    "Tests",
    "Documents",
]

ESSENTIAL_FILES = [
    "CLI/main.py",
    "Core/event_bus.py",
    "Core/events.py",
    "Core/dispatcher.py",
]


def check_python_version() -> bool:
    major, minor = sys.version_info[:2]
    is_valid = (major, minor) >= (3, 12)

    status = "OK" if is_valid else "ERRO"
    print(f"[{status}] Python {major}.{minor}")

    return is_valid


def check_directories(project_root: Path) -> bool:
    missing = [
        directory
        for directory in ESSENTIAL_DIRECTORIES
        if not (project_root / directory).is_dir()
    ]

    if missing:
        for directory in missing:
            print(f"[ERRO] Pasta ausente: {directory}")
        return False

    print("[OK] Estrutura principal")
    return True


def check_files(project_root: Path) -> bool:
    missing = [
        file_path
        for file_path in ESSENTIAL_FILES
        if not (project_root / file_path).is_file()
    ]

    if missing:
        for file_path in missing:
            print(f"[ERRO] Arquivo ausente: {file_path}")
        return False

    print("[OK] Arquivos essenciais")
    return True


def run_doctor() -> int:
    project_root = Path(__file__).resolve().parent.parent

    print("\nGENESIS DOCTOR v1\n")

    checks = [
        check_python_version(),
        check_directories(project_root),
        check_files(project_root),
    ]

    healthy = all(checks)

    if healthy:
        print("\nStatus: SAUDÁVEL")
        return 0

    print("\nStatus: PROBLEMAS ENCONTRADOS")
    return 1
