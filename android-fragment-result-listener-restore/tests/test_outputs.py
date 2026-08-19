"""Verification tests for android-fragment-result-listener-restore.
Fixed R05 Information isolation and R07 Reward-hacking by embedding expected outputs and avoiding agent-controlled build.sh/run.sh exposure.
Fixed R11 Verification efficiency by building jar once per session fixture.
Fixed R01/R02/R03 Spec sufficiency by explicitly defining SET_RESULT ignore for missing fragment in instruction.md (see instruction.md line 10).
"""

import subprocess
import shutil
from pathlib import Path
import pytest

SCENARIO_PATH = Path("/app/scenario.txt")
OUTPUT_PATH = Path("/app/output.txt")
BUILD_DIR = Path("/tmp/build")
JAR_PATH = BUILD_DIR / "app.jar"
EXPECTED_DIR = Path("/tests/expected")
HIDDEN_BACKUP = Path("/tmp/.hidden_expected_backup_for_tbench")

CASE_DATA = {
    'simple_add': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={}\nbackstack=[]\n'),
    'listener_registration': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home reqKey\nCOMMIT t2\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[reqKey] pending={} delivered={}\nbackstack=[]\n'),
    'result_delivered_when_listener_exists': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v1\nCOMMIT t3\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={k1=v1}\nbackstack=[]\n'),
    'result_queued_when_no_listener': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nCOMMIT t2\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={k1=v1} delivered={}\nbackstack=[]\n'),
    'pending_delivered_when_listener_added_later': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nCOMMIT t2\nBEGIN t3\nSET_RESULT_LISTENER t3 Home k1\nCOMMIT t3\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={k1=v1}\nbackstack=[]\n'),
    'clear_listener': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nCLEAR_RESULT_LISTENER t3 Home k1\nCOMMIT t3\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={}\nbackstack=[]\n'),
    'remove_clears_listeners_and_pending': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v1\nCOMMIT t3\nBEGIN t4\nREMOVE t4 Home\nCOMMIT t4\nQUERY\n', 'container=main fragments=[]\nbackstack=[]\n'),
    'replace_captures_result_state': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v1\nCOMMIT t3\nBEGIN t4\nREPLACE t4 main Profile\nADD_TO_BACK_STACK t4 profile\nCOMMIT t4\nPOP NONE\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={k1=v1}\nbackstack=[]\n'),
    'pop_named_uses_last': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nREPLACE t2 main A\nADD_TO_BACK_STACK t2 dup\nCOMMIT t2\nBEGIN t3\nREPLACE t3 main B\nADD_TO_BACK_STACK t3 other\nCOMMIT t3\nBEGIN t4\nREPLACE t4 main C\nADD_TO_BACK_STACK t4 dup\nCOMMIT t4\nPOP dup\nQUERY\n', 'container=main fragments=[B]\nfragment=B listeners=[] pending={} delivered={}\nbackstack=[dup, other]\n'),
    'pop_missing_is_noop': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nREPLACE t2 main Profile\nADD_TO_BACK_STACK t2 profile\nCOMMIT t2\nPOP ghost\nQUERY\n', 'container=main fragments=[Profile]\nfragment=Profile listeners=[] pending={} delivered={}\nbackstack=[profile]\n'),
    'rotate_retains_listeners_and_pending_for_backstacked': ('BEGIN t1\nADD t1 main Home\nADD_TO_BACK_STACK t1 home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nADD_TO_BACK_STACK t2 listener\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v1\nCOMMIT t3\nROTATE\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[k1] pending={} delivered={}\nbackstack=[home, listener]\n'),
    'rotate_drops_non_backstacked_result': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nROTATE\nQUERY\n', 'container=main fragments=[]\nbackstack=[]\n'),
    'queued_result_survives_rotate_if_backstacked': ('BEGIN t1\nADD t1 main Home\nADD_TO_BACK_STACK t1 home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nADD_TO_BACK_STACK t2 result\nCOMMIT t2\nROTATE\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={k1=v1} delivered={}\nbackstack=[home, result]\n'),
    'anon_backstack_label': ('BEGIN t1\nADD t1 main Home\nADD_TO_BACK_STACK t1 NONE\nCOMMIT t1\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={}\nbackstack=[anon]\n'),
    'multi_query_blank_line': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nQUERY\nBEGIN t2\nADD t2 main Profile\nCOMMIT t2\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={}\nbackstack=[]\n\ncontainer=main fragments=[Home, Profile]\nfragment=Home listeners=[] pending={} delivered={}\nfragment=Profile listeners=[] pending={} delivered={}\nbackstack=[]\n'),
    'pending_overwrite': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v2\nCOMMIT t3\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={k1=v2} delivered={}\nbackstack=[]\n'),
    'ignore_missing_fragment': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Ghost k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Ghost k1 v1\nCOMMIT t3\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={}\nbackstack=[]\n'),
    'case_sensitive_pop': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nREPLACE t2 main A\nADD_TO_BACK_STACK t2 Test\nCOMMIT t2\nBEGIN t3\nREPLACE t3 main B\nADD_TO_BACK_STACK t3 test\nCOMMIT t3\nPOP test\nQUERY\n', 'container=main fragments=[A]\nfragment=A listeners=[] pending={} delivered={}\nbackstack=[Test]\n'),
    'case_sensitive_pop_noop': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nREPLACE t2 main A\nADD_TO_BACK_STACK t2 Test\nCOMMIT t2\nPOP TEST\nQUERY\n', 'container=main fragments=[A]\nfragment=A listeners=[] pending={} delivered={}\nbackstack=[Test]\n'),
    'multi_container_sorting': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nADD t2 second Other\nCOMMIT t2\nBEGIN t3\nADD t3 alpha Alpha\nCOMMIT t3\nQUERY\n', 'container=alpha fragments=[Alpha]\ncontainer=main fragments=[Home]\ncontainer=second fragments=[Other]\nfragment=Alpha listeners=[] pending={} delivered={}\nfragment=Home listeners=[] pending={} delivered={}\nfragment=Other listeners=[] pending={} delivered={}\nbackstack=[]\n'),
    'multiple_keys': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT_LISTENER t3 Home k2\nCOMMIT t3\nBEGIN t4\nSET_RESULT t4 Home k1 v1\nCOMMIT t4\nBEGIN t5\nSET_RESULT t5 Home k2 v2\nCOMMIT t5\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={k1=v1, k2=v2}\nbackstack=[]\n'),
    'remove_pop_restore_result': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT_LISTENER t2 Home k1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k1 v1\nCOMMIT t3\nBEGIN t4\nREMOVE t4 Home\nADD_TO_BACK_STACK t4 rem\nCOMMIT t4\nPOP rem\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={} delivered={k1=v1}\nbackstack=[]\n'),
    'rotate_mixed_backstacked_non': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nCOMMIT t2\nBEGIN t3\nADD t3 main Other\nADD_TO_BACK_STACK t3 other\nCOMMIT t3\nBEGIN t4\nSET_RESULT t4 Other k2 v2\nADD_TO_BACK_STACK t4 res\nCOMMIT t4\nROTATE\nQUERY\n', 'container=main fragments=[Other]\nfragment=Other listeners=[] pending={k2=v2} delivered={}\nbackstack=[other, res]\n'),
    'pending_multiple_keys_overwrite': ('BEGIN t1\nADD t1 main Home\nCOMMIT t1\nBEGIN t2\nSET_RESULT t2 Home k1 v1\nCOMMIT t2\nBEGIN t3\nSET_RESULT t3 Home k2 v2\nCOMMIT t3\nBEGIN t4\nSET_RESULT t4 Home k1 v3\nCOMMIT t4\nQUERY\n', 'container=main fragments=[Home]\nfragment=Home listeners=[] pending={k1=v3, k2=v2} delivered={}\nbackstack=[]\n'),
}

CASE_NAMES = [
    'simple_add',
    'listener_registration',
    'result_delivered_when_listener_exists',
    'result_queued_when_no_listener',
    'pending_delivered_when_listener_added_later',
    'clear_listener',
    'remove_clears_listeners_and_pending',
    'replace_captures_result_state',
    'pop_named_uses_last',
    'pop_missing_is_noop',
    'rotate_retains_listeners_and_pending_for_backstacked',
    'rotate_drops_non_backstacked_result',
    'queued_result_survives_rotate_if_backstacked',
    'anon_backstack_label',
    'multi_query_blank_line',
    'pending_overwrite',
    'ignore_missing_fragment',
    'case_sensitive_pop',
    'case_sensitive_pop_noop',
    'multi_container_sorting',
    'multiple_keys',
    'remove_pop_restore_result',
    'rotate_mixed_backstacked_non',
    'pending_multiple_keys_overwrite',
]

@pytest.fixture(scope="session", autouse=True)
def hide_expected_dir():
    """R05/R07 fix: move /tests/expected away during verification so agent-controlled code cannot read expected outputs."""
    moved = False
    if EXPECTED_DIR.exists():
        if HIDDEN_BACKUP.exists():
            shutil.rmtree(HIDDEN_BACKUP, ignore_errors=True)
        # Move away
        try:
            shutil.move(str(EXPECTED_DIR), str(HIDDEN_BACKUP))
            moved = True
        except Exception:
            # Fallback: chmod 000
            try:
                EXPECTED_DIR.chmod(0o000)
                moved = True
            except Exception:
                moved = False
    yield
    # Restore after session
    try:
        if moved:
            if EXPECTED_DIR.exists():
                shutil.rmtree(EXPECTED_DIR, ignore_errors=True)
            if HIDDEN_BACKUP.exists():
                shutil.move(str(HIDDEN_BACKUP), str(EXPECTED_DIR))
                EXPECTED_DIR.chmod(0o755)
    except Exception:
        pass

@pytest.fixture(scope="session")
def built_jar(hide_expected_dir):
    """R11 fix: build jar once per session with direct kotlinc, not via agent-controlled build.sh, and reuse for all scenarios."""
    # Clean previous build to avoid invalid jar path error
    import shutil as _shutil
    _shutil.rmtree(str(BUILD_DIR), ignore_errors=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    # Find kotlin sources directly - avoid calling /app/src/build.sh which is agent-controlled
    find_result = subprocess.run(
        ["bash", "-c", "find /app/src -name '*.kt'"],
        capture_output=True, text=True, timeout=30
    )
    kt_files = [line.strip() for line in find_result.stdout.splitlines() if line.strip()]
    assert kt_files, "No Kotlin sources found in /app/src"
    # Use same build invocation as /app/src/build.sh to avoid invalid jar path with absolute output
    build_cmd = ["bash", "-c", "kotlinc -d /tmp/build/app.jar $(find /app/src -name '*.kt')"]
    build_result = subprocess.run(
        build_cmd,
        capture_output=True, text=True, timeout=120
    )
    assert build_result.returncode == 0, (
        f"kotlinc build failed:\nSTDOUT:\n{build_result.stdout}\nSTDERR:\n{build_result.stderr}"
    )
    assert JAR_PATH.exists(), "Jar not built at /app/build/app.jar"
    yield str(JAR_PATH)

def run_app(scenario_text, jar_path):
    SCENARIO_PATH.write_text(scenario_text)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    # R05/R07: ensure expected dir remains hidden during MainKt execution
    # (hide_expected_dir fixture already moved it, but double-check)
    # Do NOT use /app/src/run.sh - it is agent-controlled and could read /tests/expected
    result = subprocess.run(
        [
            "java",
            "-cp",
            f"{jar_path}:/opt/kotlinc/lib/kotlin-stdlib.jar",
            "com.example.app.MainKt",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"MainKt failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert OUTPUT_PATH.exists(), "Agent must produce /app/output.txt"
    return OUTPUT_PATH.read_text()

@pytest.mark.parametrize("name", CASE_NAMES)
def test_scenario(name, built_jar):
    scenario, expected = CASE_DATA[name]
    actual = run_app(scenario, built_jar)
    assert actual.strip() == expected.strip(), (
        f"Mismatch for {name}\nExpected:\n{expected}\nActual:\n{actual}"
    )
