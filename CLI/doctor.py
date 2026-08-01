from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from Core.result import Result


ESSENTIAL_DIRECTORIES = [
    "Core",
    "Engines",
    "CLI",
    "Tests",
    "Documents",
    "Blueprints",
]

ESSENTIAL_FILES = [
    "CLI/main.py",
    "CLI/doctor.py",
    "Core/event_bus.py",
    "Core/events.py",
    "Core/dispatcher.py",
    "Core/registry.py",
    "Core/result.py",
    "Core/Orchestrator/orchestrator.py",
]

ESSENTIAL_BLUEPRINTS = [
    "GenesisCLI.md",
    "GenesisOrchestrator.md",
    "GenesisResult.md",
    "GenesisDoctorV2.md",
]

CHECK_WEIGHTS = {
    "python": 15,
    "directories": 15,
    "files": 15,
    "blueprints": 15,
    "git": 20,
    "tests": 20,
}


def check_python_version() -> bool:
    major, minor = sys.version_info[:2]
    is_valid = (major, minor) >= (3, 12)

    status = "OK" if is_valid else "ERRO"
    print(f"Python ............... {status} ({major}.{minor})")

    return is_valid


def check_directories(project_root: Path) -> bool:
    missing = [
        directory
        for directory in ESSENTIAL_DIRECTORIES
        if not (project_root / directory).is_dir()
    ]

    if missing:
        print("Estrutura ............ ERRO")
        for directory in missing:
            print(f"  Pasta ausente: {directory}")
        return False

    print("Estrutura ............ OK")
    return True


def check_files(project_root: Path) -> bool:
    missing = [
        file_path
        for file_path in ESSENTIAL_FILES
        if not (project_root / file_path).is_file()
    ]

    if missing:
        print("Arquivos ............. ERRO")
        for file_path in missing:
            print(f"  Arquivo ausente: {file_path}")
        return False

    print("Arquivos ............. OK")
    return True


def check_blueprints(project_root: Path) -> bool:
    blueprints_directory = project_root / "Blueprints"

    missing = [
        blueprint
        for blueprint in ESSENTIAL_BLUEPRINTS
        if not (blueprints_directory / blueprint).is_file()
    ]

    if missing:
        print("Blueprints ........... ERRO")
        for blueprint in missing:
            print(f"  Blueprint ausente: {blueprint}")
        return False

    print("Blueprints ........... OK")
    return True


def check_git_status(project_root: Path) -> bool:
    try:
        process = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Git Status ........... ERRO")
        return False

    is_clean = not process.stdout.strip()
    status = "LIMPO" if is_clean else "ALTERAÇÕES PENDENTES"

    print(f"Git Status ........... {status}")
    return is_clean


def count_tests(project_root: Path) -> int:
    tests_directory = project_root / "Tests"
    total = 0

    if not tests_directory.is_dir():
        return total

    for test_file in tests_directory.glob("test_*.py"):
        try:
            tree = ast.parse(
                test_file.read_text(encoding="utf-8"),
                filename=str(test_file),
            )
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        total += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )

    return total


def check_tests(project_root: Path) -> bool:
    total = count_tests(project_root)
    is_valid = total > 0

    status = str(total) if is_valid else "NENHUM"
    print(f"Testes ............... {status}")

    return is_valid


def calculate_health_score(checks: dict[str, bool]) -> int:
    return sum(
        CHECK_WEIGHTS[name]
        for name, passed in checks.items()
        if passed
    )


def classify_health(score: int) -> str:
    if score == 100:
        return "SAUDÁVEL"

    if score >= 80:
        return "BOM"

    if score >= 60:
        return "ATENÇÃO"

    return "CRÍTICO"


def run_doctor() -> Result:
    project_root = Path(__file__).resolve().parent.parent

    print("\n" + "=" * 50)
    print("GENESIS DOCTOR v2")
    print("=" * 50 + "\n")

    checks = {
        "python": check_python_version(),
        "directories": check_directories(project_root),
        "files": check_files(project_root),
        "blueprints": check_blueprints(project_root),
        "git": check_git_status(project_root),
        "tests": check_tests(project_root),
    }

    score = calculate_health_score(checks)
    classification = classify_health(score)
    healthy = score == 100

    print(f"\nHealth Score ......... {score}/100")
    print(f"Status ............... {classification}")

    data = {
        "healthy": healthy,
        "score": score,
        "classification": classification,
        "checks": checks,
        "test_count": count_tests(project_root),
    }

    if healthy:
        return Result.success(
            message="Sistema saudável",
            data=data,
        )

    return Result.error(
        message="Problemas encontrados",
        data=data,
    )
