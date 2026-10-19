import json
import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
load_dotenv()
MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3

def make_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set - check .env.")
        sys.exit(1)
    return genai.Client(api_key=api_key)

ACTION_ITEMS_SCHEMA = {
    "type": "object",
    "properties": {"items": {
    "type": "array",
    "items": {"type": "object",
        "properties": {
            "owner": {"type": "string"},
            "task": {"type": "string"},
            "deadline": {"type": "string"}},
            "required": ["owner", "task", "deadline"]}}},
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
    return (
    "Extract the action items from these notes.\n\n"
    "--- NOTES START ---\n"
    + notes
    + "\n--- NOTES END ---"
    )

def attempt_extract(client, notes, feedback=None):
    contents = build_user_content(notes)
    if feedback:
        contents += (
            "\n\nYour previous response failed "
            "validation with this error:\n"
            + feedback
            + "\nReturn corrected data only."
        )
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=ACTION_ITEMS_SCHEMA,
        ),
    )
    data = json.loads(response.text)
    result = ActionItems.model_validate(data)
    return result, response.usage_metadata

def extract_validated(client, notes):
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

if __name__ == "__main__":
    main()
