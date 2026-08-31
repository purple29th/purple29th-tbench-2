#!/usr/bin/env python3
"""
Repository-level task doctor for TerminalBench task folders.
Catches invalid or contaminated task folders before submission.

Interface:
    python tools/task_doctor.py TASK_DIR
    python tools/task_doctor.py TASK_DIR --json

Checks:
- Parse task.toml using stdlib tomllib
- Verify required files/dirs exist
- Verify task name matches directory
- Verify timeout/resource values valid (>0)
- Detect README.md / instruction.md references to sibling task names (contamination)
- Reports every problem in one run, file-specific messages
- Exit 0 valid, nonzero invalid, never modifies task
"""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

REQUIRED_FILES = [
    "task.toml",
    "instruction.md",
    "README.md",
    "environment/Dockerfile",
]
REQUIRED_DIRS = ["tests", "environment"]


def _load_toml(toml_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    issues = []
    try:
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        return data, issues
    except FileNotFoundError:
        issues.append(
            {"file": "task.toml", "message": f"task.toml not found at {toml_path}"}
        )
        return {}, issues
    except Exception as e:
        issues.append(
            {"file": "task.toml", "message": f"Failed to parse task.toml: {e}"}
        )
        return {}, issues


def _get_repo_root(task_dir: Path) -> Path:
    candidate = task_dir.parent
    for p in [task_dir.parent, task_dir.parent.parent]:
        if (p / ".git").exists() or (p / "README.md").exists():
            return p
    return candidate


def _list_sibling_task_names(repo_root: Path, current_task_dir: Path) -> List[str]:
    siblings = []
    try:
        for child in repo_root.iterdir():
            if not child.is_dir():
                continue
            if child.resolve() == current_task_dir.resolve():
                continue
            if child.name.startswith("."):
                continue
            if child.name in ("jobs", "tools", "tests", "skillwatch-evals"):
                continue
            if (child / "task.toml").is_file():
                siblings.append(child.name)
    except Exception:
        pass
    return siblings


def _check_required_files(task_dir: Path) -> List[Dict[str, str]]:
    issues = []
    for rel in REQUIRED_FILES:
        p = task_dir / rel
        if not p.is_file():
            issues.append({"file": rel, "message": f"Required file missing: {rel}"})
    for rel in REQUIRED_DIRS:
        p = task_dir / rel
        if not p.is_dir():
            issues.append(
                {"file": rel, "message": f"Required directory missing: {rel}"}
            )
    return issues


def _check_task_name(task_dir: Path, toml_data: Dict[str, Any]) -> List[Dict[str, str]]:
    issues = []
    dir_name = task_dir.name
    task_section = toml_data.get("task", {})
    task_name = task_section.get("name") if isinstance(task_section, dict) else None
    if not task_name:
        schema_ver = toml_data.get("schema_version") or toml_data.get("version")
        if schema_ver == "1.1" or "task" in toml_data:
            if not task_name:
                issues.append(
                    {
                        "file": "task.toml",
                        "message": "task.name missing in task.toml (required for schema_version 1.1)",
                    }
                )
        return issues
    suffix = task_name.split("/")[-1].strip()
    if not suffix:
        issues.append(
            {
                "file": "task.toml",
                "message": f"task.name '{task_name}' has empty suffix after '/'",
            }
        )
        return issues
    if suffix != dir_name:
        issues.append(
            {
                "file": "task.toml",
                "message": f"task.name '{task_name}' does not match directory '{dir_name}' (expected suffix '{dir_name}')",
            }
        )
    return issues


def _is_positive_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and v > 0


def _parse_memory_string(s: str) -> bool:
    if not isinstance(s, str):
        return False
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([KMGkmg]i?B?|B)?\s*$", s.strip())
    if not m:
        return False
    try:
        return float(m.group(1)) > 0
    except Exception:
        return False


def _check_timeouts_resources(
    task_dir: Path, toml_data: Dict[str, Any]
) -> List[Dict[str, str]]:
    issues = []

    def check_positive(path: str, value: Any):
        if not _is_positive_number(value):
            issues.append(
                {
                    "file": "task.toml",
                    "message": f"Invalid value for {path}: {value!r} (must be >0 number)",
                }
            )

    verifier = toml_data.get("verifier", {})
    if isinstance(verifier, dict):
        if "timeout_sec" in verifier:
            check_positive("verifier.timeout_sec", verifier["timeout_sec"])
        else:
            issues.append(
                {
                    "file": "task.toml",
                    "message": "verifier.timeout_sec missing in task.toml",
                }
            )
    else:
        issues.append(
            {
                "file": "task.toml",
                "message": "verifier section missing or invalid in task.toml",
            }
        )

    agent = toml_data.get("agent", {})
    if isinstance(agent, dict):
        if "timeout_sec" in agent:
            check_positive("agent.timeout_sec", agent["timeout_sec"])
        else:
            issues.append(
                {
                    "file": "task.toml",
                    "message": "agent.timeout_sec missing in task.toml",
                }
            )
    else:
        issues.append(
            {
                "file": "task.toml",
                "message": "agent section missing or invalid in task.toml",
            }
        )

    env = toml_data.get("environment", {})
    if isinstance(env, dict):
        if "build_timeout_sec" in env:
            check_positive("environment.build_timeout_sec", env["build_timeout_sec"])
        if "cpus" in env:
            check_positive("environment.cpus", env["cpus"])
        if "memory_mb" in env:
            check_positive("environment.memory_mb", env["memory_mb"])
        if "storage_mb" in env:
            check_positive("environment.storage_mb", env["storage_mb"])
        if "memory" in env:
            mem = env["memory"]
            if isinstance(mem, str):
                if not _parse_memory_string(mem):
                    issues.append(
                        {
                            "file": "task.toml",
                            "message": f"Invalid value for environment.memory: {mem!r}",
                        }
                    )
            elif not _is_positive_number(mem):
                issues.append(
                    {
                        "file": "task.toml",
                        "message": f"Invalid value for environment.memory: {mem!r}",
                    }
                )
    else:
        issues.append(
            {
                "file": "task.toml",
                "message": "environment section missing or invalid in task.toml",
            }
        )

    for section_name in ("metadata", "task"):
        sec = toml_data.get(section_name, {})
        if isinstance(sec, dict):
            for key in ("expert_time_estimate_min", "junior_time_estimate_min"):
                if key in sec:
                    check_positive(f"{section_name}.{key}", sec[key])
    return issues


def _check_contamination(
    task_dir: Path, repo_root: Path, sibling_names: List[str]
) -> List[Dict[str, str]]:
    issues = []
    for rel_file in ("README.md", "instruction.md"):
        fp = task_dir / rel_file
        if not fp.is_file():
            continue
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            issues.append(
                {"file": rel_file, "message": f"Failed to read {rel_file}: {e}"}
            )
            continue
        dir_name = task_dir.name
        for sib in sibling_names:
            if sib == dir_name:
                continue
            if (
                sib in dir_name
            ):  # avoid false positive when own name contains sibling (e.g., breakdown-voltage contains breakdown)
                continue
            if sib in content:
                issues.append(
                    {
                        "file": rel_file,
                        "message": f"{rel_file} contains reference to sibling task '{sib}' indicating copy-paste contamination",
                    }
                )
    return issues


def doctor_task(task_dir: Path, repo_root: Path | None = None) -> List[Dict[str, str]]:
    task_dir = Path(task_dir).resolve()
    repo_root = Path(repo_root).resolve() if repo_root else _get_repo_root(task_dir)
    all_issues: List[Dict[str, str]] = []
    all_issues.extend(_check_required_files(task_dir))
    toml_path = task_dir / "task.toml"
    toml_data, parse_issues = _load_toml(toml_path)
    all_issues.extend(parse_issues)
    if toml_data:
        all_issues.extend(_check_task_name(task_dir, toml_data))
        all_issues.extend(_check_timeouts_resources(task_dir, toml_data))
    sibling_names = _list_sibling_task_names(repo_root, task_dir)
    all_issues.extend(_check_contamination(task_dir, repo_root, sibling_names))
    return all_issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Task doctor for TerminalBench task folders"
    )
    parser.add_argument("task_dir", help="Path to task directory")
    parser.add_argument("--json", action="store_true", help="Output issues as JSON")
    parser.add_argument(
        "--repo-root", help="Path to repository root (auto-detected)", default=None
    )
    args = parser.parse_args()
    task_dir = Path(args.task_dir)
    if not task_dir.is_dir():
        if args.json:
            print(
                json.dumps(
                    {
                        "task_dir": str(task_dir),
                        "valid": False,
                        "issues": [
                            {
                                "file": str(task_dir),
                                "message": f"Task directory does not exist: {task_dir}",
                            }
                        ],
                    },
                    indent=2,
                )
            )
        else:
            print(f"{task_dir}: does not exist", file=sys.stderr)
        return 2
    repo_root = Path(args.repo_root) if args.repo_root else None
    issues = doctor_task(task_dir, repo_root)
    valid = len(issues) == 0
    if args.json:
        print(
            json.dumps(
                {"task_dir": str(task_dir), "valid": valid, "issues": issues}, indent=2
            )
        )
    else:
        if valid:
            print(f"{task_dir.name}: OK - task is valid")
        else:
            print(f"{task_dir.name}: {len(issues)} issue(s) found:")
            for iss in issues:
                print(f"  {iss.get('file')}: {iss.get('message')}")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
