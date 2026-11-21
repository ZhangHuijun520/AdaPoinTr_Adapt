"""Byte bindings and single-execution controls shared by the two P5 entries."""

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def clean(name):
    path = Path(name)
    require(path.is_absolute() and ".." not in path.parts, f"absolute path: {path}")
    require(not any(p.is_symlink() for p in (path, *path.parents)), f"link: {path}")
    return path


def read(record, cap):
    path = clean(record["path"])
    size = record["bytes"]
    require(type(size) is int and 0 < size <= cap, f"size limit: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as file:
        st = os.fstat(file.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_size == size, f"regular file size: {path}")
        raw = file.read(size + 1)
    require(len(raw) == size and sha(raw) == record["sha256"], f"frozen bytes: {path}")
    return raw


def read_json(path, digest, cap=65536):
    p = clean(path)
    return json.loads(read(dict(path=str(p), bytes=p.stat().st_size, sha256=digest), cap))


def args():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    return parser.parse_args()


def authorize(a, stage):
    q = read_json(a.request, a.request_sha256)
    auth = read_json(a.authorization, a.authorization_sha256)
    runtime = read_json(a.runtime, a.runtime_sha256)
    prefix = "fcsp-p5-" + stage
    require(q["schema"] == prefix + "-request-v1" and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
            and q["execution_authorized"] is False and q["single_attempt"] is True and q["automatic_retry"] is False,
            "pending single-run request")
    l = q["launch"]
    require((l["request"], l["authorization"], l["runtime"]) ==
            (a.request, a.authorization, a.runtime), "exact control paths")
    require(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
            and auth["schema"] == prefix + "-authorization-v1" and auth["request_sha256"] == a.request_sha256
            and auth["explicit_user_authorization"] is True and auth["user_authorization_text"].strip(),
            "explicit hash-bound grant")
    require(runtime == dict(schema=prefix + "-runtime-v1", request_sha256=a.request_sha256,
                            authorization_sha256=a.authorization_sha256), "one-way runtime")
    claim = clean(l["claim"])
    require(claim.is_file() and claim.stat().st_size <= 512, "bounded claim")
    expected = "CLAIMED_BEFORE_TMUX" if stage == "predict" else "CLAIMED_BEFORE_PROCESS"
    require(json.loads(claim.read_bytes()) == dict(status=expected, request_sha256=a.request_sha256), "single attempt claim")
    return q


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        append(f, value)


def append(f, value):
    f.write(json.dumps(value, allow_nan=False) + "\n")
    f.flush()


def file_record(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return dict(bytes=path.stat().st_size, sha256=h.hexdigest())
