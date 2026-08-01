import re

from Core.logger import Logger


def test_info_log(capsys):
    logger = Logger()

    logger.info("Sistema iniciado")

    output = capsys.readouterr().out.strip()

    assert "[INFO] Sistema iniciado" in output
    assert re.match(
        r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[INFO\] Sistema iniciado",
        output,
    )


def test_warning_log(capsys):
    logger = Logger()

    logger.warning("Blueprint ausente")

    output = capsys.readouterr().out.strip()

    assert "[WARNING] Blueprint ausente" in output


def test_error_log(capsys):
    logger = Logger()

    logger.error("Falha ao carregar módulo")

    output = capsys.readouterr().out.strip()

    assert "[ERROR] Falha ao carregar módulo" in output
