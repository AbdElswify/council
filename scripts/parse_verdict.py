"""Extract and validate the council-auditor's fenced-JSON verdict."""
import json
import re


VALID_VERDICTS = {"APPROVED", "NEEDS_REVISION"}
FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


class VerdictError(ValueError):
    pass


def parse(text: str) -> dict:
    matches = FENCE_RE.findall(text)
    if not matches:
        raise VerdictError("no fenced JSON block (```json ... ```) found")
    payload = matches[-1]  # last block wins (allow auditor preamble drafts)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        raise VerdictError(f"invalid JSON in verdict block: {e}") from e
    if "verdict" not in data:
        raise VerdictError("missing 'verdict' key in JSON")
    if data["verdict"] not in VALID_VERDICTS:
        raise VerdictError(
            f"verdict must be one of {sorted(VALID_VERDICTS)}; got {data['verdict']!r}"
        )
    return data
