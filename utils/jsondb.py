from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio


_locks: Dict[str, asyncio.Lock] = {}


def _lock_for(path: Path) -> asyncio.Lock:
    key = str(path.resolve()).lower()
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_ts() -> int:
    return int(time.time())


def read_json_sync(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _atomic_write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    tmp_dir = path.parent
    fd, tmp_name = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=str(tmp_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass


async def read_json(path: Path, default: Any) -> Any:
    lock = _lock_for(path)
    async with lock:
        return read_json_sync(path, default)


async def write_json(path: Path, data: Any) -> None:
    lock = _lock_for(path)
    async with lock:
        _atomic_write_json(path, data)


async def update_json(path: Path, default: Any, mutator) -> Any:
    lock = _lock_for(path)
    async with lock:
        cur = read_json_sync(path, default)
        nxt = mutator(cur)
        _atomic_write_json(path, nxt)
        return nxt


def get_user_dict(d: Dict[str, Any], user_id: int, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    key = str(user_id)
    if key not in d:
        d[key] = default if default is not None else {}
    return d[key]

