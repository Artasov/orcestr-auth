from __future__ import annotations

import ast
from pathlib import Path
import tomllib

PACKAGE = Path(__file__).parents[1] / "src" / "orcestr_auth"
PROJECT_ROOT = Path(__file__).parents[1]


def test_fastapi_imports_stay_in_the_fastapi_adapter() -> None:
    violations: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        relative = path.relative_to(PACKAGE)
        if relative.parts[0] == "fastapi":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            else:
                continue
            if any(
                name == "fastapi" or name.startswith("fastapi.")
                for name in imported
            ):
                violations.append(f"{relative}:{node.lineno}")
    assert violations == []


def test_auth_package_does_not_use_framework_http_exceptions() -> None:
    violations: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == "HTTPException"
            ):
                violations.append(f"{path.relative_to(PACKAGE)}:{node.lineno}")
    assert violations == []


def test_removed_root_cookie_adapter_does_not_return() -> None:
    assert not (PACKAGE / "cookies.py").exists()


def test_fastapi_extra_includes_its_sqlalchemy_runtime_dependency() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    fastapi_extra = project["optional-dependencies"]["fastapi"]

    assert any(requirement.startswith("fastapi") for requirement in fastapi_extra)
    assert any(requirement.startswith("sqlalchemy") for requirement in fastapi_extra)
