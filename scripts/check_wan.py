"""Validate downloaded safetensors shards by reading their headers.

A shard that is short-truncated from an interrupted download still has a valid
JSON header, so check the declared tensor byte ranges fit inside the file.
"""

from __future__ import annotations

import json
import os
import struct
from pathlib import Path

# Override for checking a copy on another machine, e.g. the 3090 after transfer:
#   WAN_DIR=/mnt/models/Wan2.1-T2V-14B python scripts/check_wan.py
ROOT = Path(os.environ.get("WAN_DIR", r"E:\Potential-gold\models\Wan2.1-T2V-14B"))


def check(path: Path) -> tuple[bool, str]:
    size = path.stat().st_size
    with path.open("rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        if n <= 0 or n > size:
            return False, f"bad header length {n} (file {size})"
        header = json.loads(f.read(n).decode("utf-8"))
    end = max(
        (v["data_offsets"][1] for k, v in header.items() if k != "__metadata__"),
        default=0,
    )
    want = 8 + n + end
    if want > size:
        return False, f"truncated: needs {want / 1e9:.2f}GB, has {size / 1e9:.2f}GB"
    return True, f"ok  {len(header) - 1} tensors, {size / 1e9:.2f}GB"


def main() -> int:
    print(f"checking: {ROOT}")
    if not ROOT.exists():
        print("directory does not exist")
        return 1
    shards = sorted(ROOT.rglob("*.safetensors"))
    if not shards:
        print("no safetensors found")
        return 1
    bad = 0
    for p in shards:
        ok, msg = check(p)
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {p.name:<46} {msg}")
    total = sum(p.stat().st_size for p in shards) / 1e9
    print(f"\n{len(shards)} shards, {total:.2f}GB, {bad} bad")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
