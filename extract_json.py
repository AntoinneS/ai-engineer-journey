import json
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from tenacity import (retry, stop_after_attempt,
                      wait_exponential_jitter, retry_if_exception)
from google.genai import errors as genai_errors

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_ATTEMPTS = 3


def is_transient(exc: BaseException) -> bool:
    """Say whether retrying could plausibly fix this error."""
    # Retry ONLY where waiting can plausibly help.
    if isinstance(exc, genai_errors.ServerError):
        return True  # 5xx - their side
    if isinstance(exc, genai_errors.ClientError):
        return exc.code == 429  # only the rate limit
    return False


@retry(
    retry=retry_if_exception(is_transient),
    wait=wait_exponential_jitter(initial=2, max=30),
    stop=stop_after_attempt(4),
    reraise=True,
)
def generate_with_retry(client, model, contents, config):
    """Call Gemini, retrying only transient failures."""
    return client.models.generate_content(
        model=model, contents=contents, config=config)


def make_client():
    """Build a Gemini client, exiting early if the key is missing."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set - check .env.")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def estimate_cost_usd(usage, in_per_1k, out_per_1k):
    """Estimate one call's USD cost from its token usage."""
    in_cost = (usage.prompt_token_count / 1000) * in_per_1k
    out_cost = (usage.candidates_token_count / 1000) * out_per_1k
    return in_cost + out_cost


ACTION_ITEMS_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "task": {"type": "string"},
                    "deadline": {"type": "string"},
                },
                "required": ["owner", "task", "deadline"],
            },
        }
    },
    "required": ["items"],
}


class ActionItem(BaseModel):
    owner: str
    task: str
    deadline: str


class ActionItems(BaseModel):
    items: list[ActionItem]


SYSTEM_INSTRUCTION = """You are an extraction engine
for meeting notes. Your only job is to find action
items and return them as structured data.
Rules:
- An action item has an owner, a task, a deadline.
- If the deadline is not stated, write "not stated".
- Do not invent owners, tasks, or deadlines.
- Ignore anything that is not an action item.
- Return data matching the provided JSON schema.
No introduction, no summary, no extra text."""


def build_user_content(notes):
    """Wrap raw notes in the fencing the prompt expects."""
    return (
        "Extract the action items from these notes.\n\n"
        "--- NOTES START ---\n"
        + notes
        + "\n--- NOTES END ---"
    )


def attempt_extract(client, notes, feedback=None):
    """Make one extraction attempt and validate its shape."""
    contents = build_user_content(notes)
    if feedback:
        contents += (
            "\n\nYour previous response failed "
            "validation with this error:\n"
            + feedback
            + "\nReturn corrected data only."
        )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0,
        response_mime_type="application/json",
        response_json_schema=ACTION_ITEMS_SCHEMA,
        http_options=types.HttpOptions(timeout=60_000),
    )
    response = generate_with_retry(client, MODEL, contents, config)
    data = json.loads(response.text)
    result = ActionItems.model_validate(data)
    return result, response.usage_metadata


def extract_validated(client, notes):
    """Retry extraction with feedback until it validates."""
    feedback = None
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result, usage = attempt_extract(
                client, notes, feedback)
            print(f"Validated on attempt {attempt}.")
            return result, usage
        except (json.JSONDecodeError,
                ValidationError) as e:
            last_error = e
            feedback = str(e)
            print(f"Attempt {attempt} failed "
                  f"validation: {e}")
    print("Error: output failed validation after "
          f"{MAX_ATTEMPTS} attempts: {last_error}")
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run python extract_json.py notes.txt")
        sys.exit(1)
    client = make_client()
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        notes = f.read()
    result, usage = extract_validated(client, notes)
    print(json.dumps(result.model_dump(), indent=2))
    print("------------")
    print(f"Prompt tokens: {usage.prompt_token_count}")
    print(f"Response tokens: {usage.candidates_token_count}")
    print(f"Total tokens: {usage.total_token_count}")
    in_price = float(os.getenv("GEMINI_PRICE_IN_PER_1K", "0"))
    out_price = float(os.getenv("GEMINI_PRICE_OUT_PER_1K", "0"))
    if in_price or out_price:
        cost = estimate_cost_usd(usage, in_price, out_price)
        print(f"Est. cost this run: ${cost:.6f}")
    else:
        print("Cost: set GEMINI_PRICE_IN_PER_1K / "
              "GEMINI_PRICE_OUT_PER_1K in .env to estimate.")


if __name__ == "__main__":
    main()
