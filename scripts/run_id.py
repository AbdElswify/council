"""Generate a council run identifier: ISO-like timestamp + 4-char random suffix."""
import secrets
from datetime import datetime, timezone


def new_run_id() -> str:
    # Timezone-aware UTC; datetime.utcnow() is deprecated in Python 3.12+.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"{ts}-{suffix}"
