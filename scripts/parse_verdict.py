"""Extract and validate the council-auditor's fenced-JSON verdict."""
import json
import re


VALID_VERDICTS = {"APPROVED", "NEEDS_REVISION"}
VALID_PASSES = {1, 2}
VALID_SEVERITIES = {"blocker", "should-fix"}
# Opening fence: ```json then optional trailing spaces/tabs and a line break
# (LF or CRLF). Body is captured non-greedily. Closing fence: the newline
# before ``` is OPTIONAL, so a block whose JSON ends right against the closing
# fence (no trailing blank line) still parses. Trailing whitespace before the
# closing ``` is tolerated. JSON itself ignores surrounding whitespace.
FENCE_RE = re.compile(r"```json[ \t]*\r?\n(.*?)\r?\n?[ \t]*```", re.DOTALL)


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

    # verdict (required, str, in VALID_VERDICTS)
    if "verdict" not in data:
        raise VerdictError("missing 'verdict' key in JSON")
    if data["verdict"] not in VALID_VERDICTS:
        raise VerdictError(
            f"verdict must be one of {sorted(VALID_VERDICTS)}; got {data['verdict']!r}"
        )

    # round (required, int, >= 1). bool is a subclass of int in Python; exclude it.
    if "round" not in data:
        raise VerdictError("missing 'round' key in JSON")
    if not isinstance(data["round"], int) or isinstance(data["round"], bool):
        raise VerdictError(f"round must be an int; got {type(data['round']).__name__}")
    if data["round"] < 1:
        raise VerdictError(f"round must be >= 1; got {data['round']}")

    # pass (required, int, in {1, 2}).
    if "pass" not in data:
        raise VerdictError("missing 'pass' key in JSON")
    if not isinstance(data["pass"], int) or isinstance(data["pass"], bool):
        raise VerdictError(f"pass must be an int; got {type(data['pass']).__name__}")
    if data["pass"] not in VALID_PASSES:
        raise VerdictError(f"pass must be 1 or 2; got {data['pass']}")

    # findings (required, list)
    if "findings" not in data:
        raise VerdictError("missing 'findings' key in JSON")
    if not isinstance(data["findings"], list):
        raise VerdictError(
            f"findings must be a list; got {type(data['findings']).__name__}"
        )

    # findings semantics: empty if and only if APPROVED. This mirrors the
    # rule the council-auditor prompt promises, so a verdict that contradicts
    # its own findings (e.g. APPROVED with open findings) is rejected here
    # rather than silently trusted by the Mayor.
    findings = data["findings"]
    if data["verdict"] == "APPROVED" and findings:
        raise VerdictError("an APPROVED verdict must have empty findings []")
    if data["verdict"] == "NEEDS_REVISION" and not findings:
        raise VerdictError(
            "a NEEDS_REVISION verdict must list at least one finding"
        )

    # findings element shape: each is an object with severity (blocker|
    # should-fix) and issue (str); loc is optional but must be a str if given.
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            raise VerdictError(f"findings[{i}] must be an object; got {type(f).__name__}")
        if "severity" not in f:
            raise VerdictError(f"findings[{i}] missing 'severity'")
        if f["severity"] not in VALID_SEVERITIES:
            raise VerdictError(
                f"findings[{i}].severity must be one of {sorted(VALID_SEVERITIES)}; "
                f"got {f['severity']!r}"
            )
        if "issue" not in f:
            raise VerdictError(f"findings[{i}] missing 'issue'")
        if not isinstance(f["issue"], str):
            raise VerdictError(
                f"findings[{i}].issue must be a string; got {type(f['issue']).__name__}"
            )
        if "loc" in f and not isinstance(f["loc"], str):
            raise VerdictError(
                f"findings[{i}].loc must be a string; got {type(f['loc']).__name__}"
            )

    # contract_concerns (required, list)
    if "contract_concerns" not in data:
        raise VerdictError("missing 'contract_concerns' key in JSON")
    if not isinstance(data["contract_concerns"], list):
        raise VerdictError(
            f"contract_concerns must be a list; got {type(data['contract_concerns']).__name__}"
        )

    # notes (optional, str if present)
    if "notes" in data and not isinstance(data["notes"], str):
        raise VerdictError(
            f"notes must be a string; got {type(data['notes']).__name__}"
        )

    return data
