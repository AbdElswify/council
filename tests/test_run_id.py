import re
import run_id

RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}-[a-z0-9]{4}$")

def test_format():
    assert RUN_ID_PATTERN.match(run_id.new_run_id())

def test_two_calls_differ():
    # Suffix randomness should make collisions astronomically unlikely
    assert run_id.new_run_id() != run_id.new_run_id()
