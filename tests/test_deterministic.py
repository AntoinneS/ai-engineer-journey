"""Deterministic guards: these must pass offline, every run."""
from google.genai import errors as genai_errors

from eval import normalise, score_case
from extract_json import (build_user_content,
                            estimate_cost_usd, is_transient)

class FakeUsage:
    """Stand-in carrying only the fields the cost helper reads."""
    prompt_token_count = 1000
    candidates_token_count = 500

def test_cost_helper_math():
    """Cost is tokens/1000 x price-per-1k, per direction."""
    assert estimate_cost_usd(FakeUsage(), 0.001, 0.002) \
        == 0.001 + 0.001

def test_is_transient_only_retries_what_waiting_fixes():
    """429 and 5xx retry; other client errors do not."""
    assert is_transient(
        genai_errors.ClientError(429, {}, None)) is True
    assert is_transient(
        genai_errors.ClientError(404, {}, None)) is False
    assert is_transient(
        genai_errors.ServerError(503, {}, None)) is True

def test_build_user_content_fences_the_notes():
    """Notes stay inside the markers the prompt relies on."""
    out = build_user_content("hello")
    assert "--- NOTES START ---" in out
    assert "--- NOTES END ---" in out
    assert "hello" in out

def test_normalise_ignores_formatting_only():
    """Casing and trailing periods pass; different facts fail."""
    assert normalise(" Send the Report. ") \
        == normalise("send the report")

def test_score_case_punishes_fabrication():
    """An invented item scores zero, not partial credit."""
    expected = {"items": []}
    actual = {"items": [{"owner": "X", "task": "Y",
                        "deadline": "Z"}]}
    counts, _ = score_case(expected, actual)
    assert all(v == 0 for v in counts.values())
