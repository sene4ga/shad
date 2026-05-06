"""Shared fixtures for pipeline tests."""
from pathlib import Path

import pytest
import yaml


PIPELINE_FILE = Path(__file__).parent / "pipeline.yml"


@pytest.fixture(scope="session")
def pipeline() -> dict:
    """Load and parse the student's pipeline.yml."""
    if not PIPELINE_FILE.exists():
        pytest.fail(
            f"Файл {PIPELINE_FILE.name} не найден. "
            "Создайте его на основе pipeline.yml.template и решите задачу."
        )

    try:
        with open(PIPELINE_FILE) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"pipeline.yml — невалидный YAML: {e}")

    if not isinstance(data, dict):
        pytest.fail(
            "pipeline.yml на верхнем уровне должен быть словарём (mapping). "
            f"Получено: {type(data).__name__}"
        )

    return data # type: ignore


@pytest.fixture(scope="session")
def jobs(pipeline: dict) -> dict:
    """Return only top-level keys that are jobs (not config keys, not hidden templates)."""
    reserved = {
        "stages", "variables", "cache", "include", "default",
        "workflow", "image", "services", "before_script", "after_script",
    }
    return {
        name: cfg for name, cfg in pipeline.items()
        if name not in reserved
        and not name.startswith(".")
        and isinstance(cfg, dict)
    }


@pytest.fixture(scope="session")
def templates(pipeline: dict) -> dict:
    """Return hidden job templates (names starting with .)."""
    return {
        name: cfg for name, cfg in pipeline.items()
        if name.startswith(".") and isinstance(cfg, dict)
    }
