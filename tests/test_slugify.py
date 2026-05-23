# tests/test_slugify.py
import slugify

def test_basic():
    assert slugify.slugify("Hello World") == "hello-world"

def test_strips_special_chars():
    assert slugify.slugify("Fix bug #42!") == "fix-bug-42"

def test_truncates_to_40():
    assert len(slugify.slugify("a" * 100)) == 40

def test_empty_returns_placeholder():
    assert slugify.slugify("") == "task"

def test_whitespace_only_returns_placeholder():
    assert slugify.slugify("   \t\n  ") == "task"

def test_collapses_runs_of_non_alnum():
    assert slugify.slugify("a !!! b") == "a-b"
