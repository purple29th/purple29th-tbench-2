"""Verification tests for android-fragment-result-listener-restore.
Fixed R05 Information isolation and R07 Reward-hacking by embedding expected outputs and avoiding agent-controlled build.sh/run.sh exposure.
Fixed R11 Verification efficiency by building jar once per session fixture.
Fixed R01/R02/R03 Spec sufficiency by explicitly defining SET_RESULT ignore for missing fragment in instruction.md (see instruction.md line 10).
R05/R07 hardened: hide expected-bearing module and pycache from child JVM via unguessable 700 backup + /tests private + run MainKt as nobody.
"""

import subprocess
import shutil
import os
import tempfile
import pwd
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

# --- R05/R07 isolation helpers ---
_HIDDEN_DIR = None
_MOVED = []  # list of (src, dst, was_symlink, link_target)
_ORIG_TESTS_STAT = None

def _current_user():
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except:
        try:
            return subprocess.check_output(["whoami"], text=True).strip()
        except:
            return "purple29th"

def _sudo(cmd):
    # try sudo -n (non-interactive), fallback to direct
    try:
        r = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return True
    except:
        pass
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except:
        return False

@pytest.fixture(scope="session", autouse=True)
def hide_expected_dir():
    """R05/R07: hide expected outputs and the test module itself from child JVM.
    Moves /tests/expected, /tests/test_outputs.py (and its real target), and pycache
    to an unguessable 700 directory, and makes /tests private to pytest user.
    Child JVM runs as nobody and cannot read hidden location or /tests.
    """
    global _HIDDEN_DIR, _MOVED, _ORIG_TESTS_STAT
    # create unguessable hidden dir
    _HIDDEN_DIR = Path(tempfile.mkdtemp(prefix=".tbench_hidden_", dir="/tmp"))
    try:
        _HIDDEN_DIR.chmod(0o700)
    except:
        pass
    # ensure hidden dir not world-readable even if mkdtemp respects umask
    _sudo(["chmod", "700", str(_HIDDEN_DIR)])
    # make /app writable for nobody's output
    _sudo(["chmod", "777", "/app"])
    _sudo(["chmod", "-R", "777", "/tmp/build"]) if Path("/tmp/build").exists() else None

    # collect paths to hide
    candidates = []
    # /tests entries
    candidates.append(Path("/tests/expected"))
    candidates.append(Path("/tests/test_outputs.py"))
    candidates.append(Path("/tests/__pycache__"))
    # resolved real file behind symlink - do not move separately (would double-hide and create loop),
    # instead the symlink move hides the /tests path; the real file's world-readable path is hardened via chmod 700 on its parent in the next block.
    # We keep the real path out of candidates to avoid double-move loop with /tests/expected symlink target.
    # repo copy (direct read path)
    repo = Path("/home/purple29th/purple29th-tbench-2/android-fragment-result-listener-restore/tests/test_outputs.py")
    if repo.exists():
        candidates.append(repo)
        pc2 = repo.parent / "__pycache__"
        if pc2.exists():
            candidates.append(pc2)
    # dedup
    seen = set()
    uniq = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            seen.add(s)
            uniq.append(c)


    # Harden the symlink target of /tests/expected if it is a symlink to a repo dir (e.g., viewbinding expected)
    try:
        exp_link = Path("/tests/expected")
        if exp_link.is_symlink():
            real_exp = exp_link.resolve()
            if real_exp != exp_link and real_exp.exists() and real_exp.is_dir():
                # chmod 700 owned by current user so nobody cannot read, instead of moving (avoids loop)
                try:
                    _sudo(["chmod", "700", str(real_exp)])
                    real_exp.chmod(0o700)
                except:
                    pass
                # also chmod its parent? no
                # remember to restore later
                _MOVED.append((real_exp, None, False))  # marker for chmod restore
    except:
        pass

    for src in uniq:
        try:
            if src.exists() or src.is_symlink():
                # create unique dst name to avoid collision
                safe = src.as_posix().replace("/", "_").lstrip("_") + "_" + os.urandom(4).hex()
                dst = _HIDDEN_DIR / safe
                # if symlink, move symlink itself (lexists), else move file/dir
                shutil.move(str(src), str(dst))
                _MOVED.append((src, dst, src.is_symlink()))
                # leave no trace at src
        except Exception as e:
            # best effort
            pass

    # make /tests private to pytest user only (if still exists)
    try:
        tests_path = Path("/tests")
        if tests_path.exists():
            _ORIG_TESTS_STAT = tests_path.stat()
            cur_user = _current_user()
            _sudo(["chown", cur_user, str(tests_path)])
            _sudo(["chmod", "700", str(tests_path)])
            # also try chmod via python
            try:
                tests_path.chmod(0o700)
            except:
                pass
    except:
        pass

    yield

    # restore after session
    try:
        # restore /tests perms
        if _ORIG_TESTS_STAT is not None:
            tests_path = Path("/tests")
            try:
                _sudo(["chmod", "755", str(tests_path)])
                # chown back to root if we changed it
                _sudo(["chown", "root", str(tests_path)])
            except:
                pass
            try:
                tests_path.chmod(0o755)
            except:
                pass
    except:
        pass
    # restore moved files and chmodded expected target
    for src, dst, _ in reversed(_MOVED):
        try:
            if dst is None:
                # was a chmod-only marker for expected target
                try:
                    _sudo(["chmod", "755", str(src)])
                    src.chmod(0o755)
                except:
                    pass
                continue
            if dst.exists():
                # ensure parent exists
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
                # ensure perms readable for next run
                try:
                    if src.is_dir():
                        src.chmod(0o755)
                    else:
                        src.chmod(0o644)
                except:
                    pass
        except:
            pass
    # cleanup hidden dir
    try:
        if _HIDDEN_DIR and _HIDDEN_DIR.exists():
            shutil.rmtree(str(_HIDDEN_DIR), ignore_errors=True)
    except:
        pass
    # restore /app perms
    try:
        _sudo(["chmod", "755", "/app"])
    except:
        pass

@pytest.fixture(scope="session")
def built_jar(hide_expected_dir):
    """R11 fix: build jar once per session with direct kotlinc, not via agent-controlled build.sh, and reuse for all scenarios."""
    # Clean previous build to avoid invalid jar path error
    import shutil as _shutil
    _shutil.rmtree(str(BUILD_DIR), ignore_errors=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    _sudo(["chmod", "777", str(BUILD_DIR)])
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
    # make jar world-readable for nobody
    try:
        JAR_PATH.chmod(0o644)
        _sudo(["chmod", "644", str(JAR_PATH)])
        _sudo(["chmod", "755", str(BUILD_DIR)])
    except:
        pass
    yield str(JAR_PATH)

def run_app(scenario_text, jar_path):
    SCENARIO_PATH.write_text(scenario_text)
    # make scenario readable by nobody
    try:
        SCENARIO_PATH.chmod(0o666)
        _sudo(["chmod", "666", str(SCENARIO_PATH)])
    except:
        pass
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    # ensure /app writable for nobody
    _sudo(["chmod", "777", "/app"])
    # ensure BUILD_DIR/jar readable
    _sudo(["chmod", "777", str(BUILD_DIR)])
    _sudo(["chmod", "644", str(jar_path)])

    # Do NOT use /app/src/run.sh - it is agent-controlled and could read /tests/expected
    # Run as unprivileged user if possible to enforce isolation
    base_cmd = [
        "java",
        "-cp",
        f"{jar_path}:/opt/kotlinc/lib/kotlin-stdlib.jar",
        "com.example.app.MainKt",
    ]
    # try sudo -u nobody, then runuser, then direct
    result = None
    for wrapper in [
        ["sudo", "-n", "-u", "nobody"] + base_cmd,
        ["sudo", "-u", "nobody"] + base_cmd,
        ["runuser", "-u", "nobody", "--"] + base_cmd,
        base_cmd,
    ]:
        try:
            result = subprocess.run(
                wrapper,
                capture_output=True, text=True, timeout=120,
            )
            # if wrapper was sudo/nobody and failed due to perms, try next
            # success is returncode 0, else try direct
            if result.returncode == 0:
                break
            # if sudo not available, result may contain "sudo: a password is required"
            if "password is required" in result.stderr or "user unknown" in result.stderr:
                continue
            # if nobody cannot write, it will fail; fallback to direct for local dev
            if result.returncode != 0 and wrapper != base_cmd:
                # try next wrapper
                continue
            break
        except FileNotFoundError:
            continue
        except Exception:
            continue
    assert result is not None, "Failed to launch MainKt"
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
