from __future__ import annotations
import logging
from contextlib import contextmanager
from typing import Any, Dict

LOGGER_NAME = "crontex.app"

def get_logger(name: str = "") -> logging.Logger:
    base = logging.getLogger(LOGGER_NAME)
    return base.getChild(name) if name else base

def _fmt(msg: str, kv: Dict[str, Any]) -> str:
    if not kv:
        return msg
    try:
        pairs = " ".join(f"{k}={repr(v)}" for k, v in kv.items())
    except Exception:
        pairs = str(kv)
    return f"{msg} | {pairs}"

def dbg(msg: str, **kv: Any) -> None:
    get_logger().debug(_fmt(msg, kv))

def info(msg: str, **kv: Any) -> None:
    get_logger().info(_fmt(msg, kv))

def warn(msg: str, **kv: Any) -> None:
    get_logger().warning(_fmt(msg, kv))

def err(msg: str, **kv: Any) -> None:
    get_logger().error(_fmt(msg, kv))

@contextmanager
def step(label: str, **kv: Any):
    log = get_logger()
    log.info(_fmt(f"[BEGIN] {label}", kv))
    try:
        yield
        log.info(_fmt(f"[END] {label}", kv))
    except Exception as e:
        log.exception(_fmt(f"[FAIL] {label}", {**kv, "error": e}))
        raise
