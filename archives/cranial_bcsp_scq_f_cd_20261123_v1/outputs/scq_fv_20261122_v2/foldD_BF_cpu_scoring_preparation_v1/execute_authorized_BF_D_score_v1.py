"""Verify and run the user-authorized Fold D CPU score once, in the foreground."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_fv_BF_D_score_v1 as score

KEY = "0f279325e0d0d3b4dc58595bfd88bdd85c70b6ccebffb6a642a14eae7ced0704"
REQUEST = HERE / "BF_D_CPU_scoring_execution_request_v1.json"
EVIDENCE = HERE / "authorized_execution_v1"
FLAGS = ["-I", "-B"]


def save(name, data):
    score.emit(EVIDENCE / name, data)


def main():
    assert score.sha(REQUEST) == KEY
    q = json.loads(REQUEST.read_bytes())
    assert q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
    assert q["counts"] == score.COUNTS and q["execution_attempts"] == 1 and q["foreground"]
    assert not EVIDENCE.exists() and not EVIDENCE.is_symlink()
    out, auth = Path(q["output"]), Path(q["authorization_path"])
    assert out == HERE / "unified_scores_v1" and not out.exists() and not out.is_symlink()
    assert auth == EVIDENCE / "score_authorization_v1.json"
    bound = [*q["implementation"].values(), *q["sidecars"], q["environment"]["python"]]
    bound += [q[k] for k in ("archive", "prediction_completion", "prediction_audit", "prediction_index",
        "reference_manifest", "historical_controls", "score_case_index", "bootstrap_indices", "protocol", "P3")]
    for r in bound:
        score.exact(r)
    cases = score.read(q["score_case_index"])["cases"]
    score.validate_cases(score.read(q["prediction_index"]), score.read(q["reference_manifest"]), cases)
    for c in cases:
        score.exact(c["point_file"])
        score.exact(c["reference"])
    python = q["environment"]["python"]["path"]
    assert q["environment"]["flags"] == FLAGS
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "2",
           "OPENBLAS_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "PYTHONDONTWRITEBYTECODE": "1"}
    package_names = list(q["environment"]["packages"])
    code = ("import importlib.metadata as m,json,sys;print(json.dumps("
            f"dict(python=sys.version,packages={{k:m.version(k) for k in {package_names!r}}})))")
    result = subprocess.run([python, *FLAGS, "-c", code], capture_output=True, check=True, timeout=15, env=env)
    actual = json.loads(result.stdout)
    assert actual == dict(python=q["environment"]["python_version"], packages=q["environment"]["packages"])
    EVIDENCE.mkdir()
    save("prelaunch_verification_v1.json", dict(status="HASHES_ENVIRONMENT_AND_FOLD_VERIFIED",
        request_sha256=KEY, static_bindings=len(bound), reference_files=105, point_files=105, environment=actual))
    save(auth.name, dict(schema="bcsp-scq-fv-BF-D-score-authorization-v1", request_sha256=KEY,
        explicit_user_authorization=True, user_authorization_text="好的，授权执行请求"))
    argv = [python, *FLAGS, q["implementation"]["scorer"]["path"], "--request", str(REQUEST),
            "--request-sha256", KEY, "--authorization", str(auth), "--authorization-sha256", score.sha(auth)]
    save("attempt_claim_v1.json", dict(status="CLAIMED_BEFORE_LOCAL_SUBPROCESS", attempt=1, request_sha256=KEY,
        authorization_sha256=score.sha(auth), command=argv, UTC=datetime.now(timezone.utc).isoformat(), automatic_retry=False))
    start = time.monotonic()
    rc, timeout, failure = None, False, None
    stdout, stderr = EVIDENCE / "stdout_v1.bin", EVIDENCE / "stderr_v1.bin"
    try:
        with stdout.open("xb") as out_stream, stderr.open("xb") as err_stream:
            worker = subprocess.Popen(argv, cwd=HERE, env=env, stdout=out_stream, stderr=err_stream)
            save("worker_started_v1.json", dict(pid=worker.pid, request_sha256=KEY))
            print(json.dumps(dict(status="UNIQUE_CPU_SCORING_STARTED", pid=worker.pid)), flush=True)
            try:
                rc = worker.wait(timeout=q["external_wall_timeout_seconds"])
            except subprocess.TimeoutExpired:
                timeout = True
                worker.kill()
                worker.wait()
                rc = 124
    except BaseException as exc:
        failure = repr(exc)
    complete = out / "completion.json"
    done = json.loads(complete.read_bytes()) if complete.is_file() else None
    failed = out / "failure.json"
    ok = rc == 0 and not timeout and not failure and not failed.exists() and done is not None and (
        done["status"] == "CPU_SCORE_COMPLETE_AWAITING_FORMAL_FREEZE" and done["request_sha256"] == KEY
        and done["counts"] == score.COUNTS and done["formal_gate_executed"] is False)
    status = dict(status="COMPLETE_AWAITING_FORMAL_FREEZE" if ok else "FAILED_STOP_NO_RETRY", request_sha256=KEY,
                  returncode=rc, timeout=timeout, error=failure, completion=done,
                  failure=json.loads(failed.read_bytes()) if failed.is_file() else None,
                  stdout_sha256=score.sha(stdout), stderr_sha256=score.sha(stderr),
                  seconds=time.monotonic()-start, formal_audit_executed=False, server_operations=0, retries=0)
    save("execution_result_v1.json",status)
    print(json.dumps(status),flush=True)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
