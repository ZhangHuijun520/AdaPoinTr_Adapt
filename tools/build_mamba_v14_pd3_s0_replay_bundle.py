#!/usr/bin/env python3
"""Build split restore media for the four archived frozen D3 S0 checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path


LOCK_MEMBER = (
    "logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1/"
    "feasibility_lock_receipt.json"
)
BASE = "mamba_v14_pd3_s0_replay_checkpoints_seed0_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class HashingReader:
    def __init__(self, source):
        self.source = source
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        data = self.source.read(size)
        self.digest.update(data)
        return data


class SplitWriter(io.RawIOBase):
    def __init__(self, output_dir: Path, chunk_bytes: int):
        self.output_dir = output_dir
        self.chunk_bytes = chunk_bytes
        self.parts: list[Path] = []
        self.current = None
        self.current_size = 0
        self.total_size = 0
        self.tar_digest = hashlib.sha256()

    def writable(self):
        return True

    def _open_next(self):
        path = self.output_dir / f"{BASE}.part-{len(self.parts):03d}"
        self.current = path.open("xb")
        self.parts.append(path)
        self.current_size = 0

    def write(self, data):
        view = memoryview(data)
        self.tar_digest.update(view)
        written = 0
        while view:
            if self.current is None or self.current_size == self.chunk_bytes:
                if self.current is not None:
                    self.current.close()
                self._open_next()
            capacity = self.chunk_bytes - self.current_size
            piece = view[:capacity]
            count = self.current.write(piece)
            if count != len(piece):
                raise OSError("Short write while creating split archive")
            self.current_size += count
            self.total_size += count
            written += count
            view = view[count:]
        return written

    def close(self):
        if self.current is not None and not self.current.closed:
            self.current.close()
        super().close()


def canonical_json(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_archive", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--chunk_mib", type=int, default=256)
    args = parser.parse_args()

    source_path = args.source_archive.resolve()
    output = args.output_dir.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if args.chunk_mib < 32:
        raise ValueError("chunk_mib must be at least 32")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError(f"Output directory must be empty: {output}")

    member_hashes = {}
    with tarfile.open(source_path, mode="r:") as source:
        lock_file = source.extractfile(LOCK_MEMBER)
        if lock_file is None:
            raise RuntimeError(f"Archive omits {LOCK_MEMBER}")
        lock_bytes = lock_file.read()
        lock = json.loads(lock_bytes)
        members = []
        expected = {}
        for fold, item in sorted(lock["folds"].items()):
            for kind in ("s0_config", "s0_checkpoint"):
                name = item[kind]["path"]
                members.append(name)
                expected[name] = item[kind]["sha256"]

        writer = SplitWriter(output, args.chunk_mib * 1024 * 1024)
        try:
            with tarfile.open(fileobj=writer, mode="w|") as target:
                for name in members:
                    member = source.getmember(name)
                    if not member.isfile():
                        raise RuntimeError(f"Expected regular file member: {name}")
                    raw = source.extractfile(member)
                    if raw is None:
                        raise RuntimeError(f"Cannot read archive member: {name}")
                    reader = HashingReader(raw)
                    target.addfile(member, reader)
                    digest = reader.digest.hexdigest()
                    if digest != expected[name]:
                        raise RuntimeError(f"Archived member hash mismatch: {name}")
                    member_hashes[name] = digest
        finally:
            writer.close()

    if not writer.parts:
        raise RuntimeError("No split parts were produced")
    parts_manifest = "".join(
        f"{sha256_file(path)}  {path.name}\n" for path in writer.parts
    )
    (output / f"{BASE}.parts.sha256").write_text(
        parts_manifest, encoding="ascii", newline="\n"
    )
    (output / f"{BASE}.parts.count").write_text(
        f"{len(writer.parts)}\n", encoding="ascii", newline="\n"
    )
    (output / f"{BASE}.bytes").write_text(
        f"{writer.total_size}\n", encoding="ascii", newline="\n"
    )
    (output / f"{BASE}.tar.sha256").write_text(
        f"{writer.tar_digest.hexdigest()}  {BASE}.tar\n",
        encoding="ascii",
        newline="\n",
    )
    member_manifest = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(member_hashes.items())
    )
    (output / f"{BASE}.members.sha256").write_text(
        member_manifest, encoding="ascii", newline="\n"
    )
    metadata = {
        "bundle_version": BASE,
        "source_archive": source_path.name,
        "source_archive_sha256": sha256_file(source_path),
        "lock_member": LOCK_MEMBER,
        "lock_member_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "chunk_mib": args.chunk_mib,
        "part_count": len(writer.parts),
        "tar_bytes": writer.total_size,
        "tar_sha256": writer.tar_digest.hexdigest(),
        "members": member_hashes,
        "purpose": "temporary observation-only P-D3 replay restore",
    }
    (output / f"{BASE}.metadata.json").write_bytes(canonical_json(metadata))
    print(f"[saved] P-D3 checkpoint restore bundle: {output}")
    print(f"[summary] parts={len(writer.parts)} tar_bytes={writer.total_size}")
    print(f"[sha256] {writer.tar_digest.hexdigest()}")


if __name__ == "__main__":
    main()
