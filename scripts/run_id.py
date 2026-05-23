"""Generate a council run identifier: ISO-like timestamp + 4-char random suffix."""
import secrets
from datetime import datetime


def new_run_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"{ts}-{suffix}"
