"""Pytest coverage for tools/task_doctor.py using temporary task directories."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from task_doctor import doctor_task, _list_sibling_task_names


def _make_valid_toml(dir_name: str) -> str:
    return f"""
schema_version = "1.1"
[task]
name = "codimango/{dir_name}"
format = "terminal_bench_single_turn"
description = "Test task"
authors = [{{ name = "Test", email = "test@example.com" }}]
[metadata]
author_name = "Test"
difficulty = "easy"
category = "software-engineering"
[verifier]
timeout_sec = 60.0
[agent]
timeout_sec = 120.0
[environment]
build_timeout_sec = 600.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
"""


def _create_minimal_valid_task(base: Path, name: str) -> Path:
    task_dir = base / name
    task_dir.mkdir(parents=True)
    (task_dir / "task.toml").write_text(_make_valid_toml(name), encoding="utf-8")
    (task_dir / "instruction.md").write_text(
        f"# {name} instruction\nDo something.", encoding="utf-8"
    )
    (task_dir / "README.md").write_text(f"# {name} README\nClean.", encoding="utf-8")
    env_dir = task_dir / "environment"
    env_dir.mkdir()
    (env_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")
    tests_dir = task_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test.sh").write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
    return task_dir


def test_valid_task(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "my-valid-task")
    assert doctor_task(task_dir, repo_root=repo_root) == []


def test_missing_required_files(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "missing-files-task")
    (task_dir / "instruction.md").unlink()
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert any("instruction.md" in i["file"] for i in issues)
    (task_dir / "environment" / "Dockerfile").unlink()
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert len(issues) >= 2


def test_missing_tests_dir(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "missing-tests-dir")
    import shutil

    shutil.rmtree(task_dir / "tests")
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert any("tests" in i["file"] for i in issues)


def test_task_name_mismatch(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "my-task")
    bad = _make_valid_toml("my-task").replace("my-task", "other-task")
    (task_dir / "task.toml").write_text(bad, encoding="utf-8")
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert any("does not match directory" in i["message"] for i in issues)


def test_invalid_timeout_values(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "bad-timeout-task")
    toml_content = """
schema_version = "1.1"
[task]
name = "codimango/bad-timeout-task"
[verifier]
timeout_sec = 0
[agent]
timeout_sec = 120.0
[environment]
build_timeout_sec = 600.0
cpus = 2
memory_mb = 4096
"""
    (task_dir / "task.toml").write_text(toml_content, encoding="utf-8")
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert any("verifier.timeout_sec" in i["message"] for i in issues)


def test_contamination_detection(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    sibling = _create_minimal_valid_task(repo_root, "sibling-task-alpha")
    current = _create_minimal_valid_task(repo_root, "current-task-beta")
    (current / "README.md").write_text(
        "Similar to sibling-task-alpha", encoding="utf-8"
    )
    issues = doctor_task(current, repo_root=repo_root)
    assert any("sibling-task-alpha" in i["message"] for i in issues)


def test_no_self_contamination(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "self-task")
    (task_dir / "README.md").write_text(
        "This is self-task and self-task does great", encoding="utf-8"
    )
    issues = doctor_task(task_dir, repo_root=repo_root)
    assert not any("sibling" in i["message"] for i in issues)


def test_json_cli_interface(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "json-test-task")
    result = subprocess.run(
        [
            sys.executable,
            "tools/task_doctor.py",
            str(task_dir),
            "--json",
            "--repo-root",
            str(repo_root),
        ],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True


def test_text_cli_and_exit_codes(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "cli-test-task")
    result = subprocess.run(
        [
            sys.executable,
            "tools/task_doctor.py",
            str(task_dir),
            "--repo-root",
            str(repo_root),
        ],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout
    (task_dir / "instruction.md").unlink()
    result2 = subprocess.run(
        [
            sys.executable,
            "tools/task_doctor.py",
            str(task_dir),
            "--repo-root",
            str(repo_root),
        ],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert result2.returncode != 0


def test_never_modifies_task(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    task_dir = _create_minimal_valid_task(repo_root, "immutable-task")
    files = list(task_dir.rglob("*"))
    before = {f: f.read_bytes() if f.is_file() else None for f in files}
    doctor_task(task_dir, repo_root=repo_root)
    for f in files:
        if f.is_file():
            assert f.read_bytes() == before[f]


def test_complex_valid_task_from_real_repo():
    real_root = Path(__file__).resolve().parent.parent
    hello = real_root / "hello-world"
    if hello.is_dir():
        assert doctor_task(hello, repo_root=real_root) == []
