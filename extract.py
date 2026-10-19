import argparse
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def make_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set - check .env file")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract action items from meeting notes.")
    parser.add_argument("notes_file", help="Path to the notes text file")
    return parser.parse_args()


def read_notes(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


SYSTEM_INSTRUCTION = """You are an extraction engine
for meeting notes. Your only job is to find action
items and return them as a list.
Rules:
- An action item has an owner, a task, a deadline.
- If the deadline is not stated, write "not stated".
- Do not invent owners, tasks, or deadlines.
- Ignore anything that is not an action item.
- Return only the list. No introduction, no summary.
Format: one item per line, exactly as:
Owner | Task | Deadline"""

FEW_SHOT = """Example notes:
Sam will file the report by Wednesday. Lee to book
the venue.
Example output:
Sam | File the report | Wednesday
Lee | Book the venue | not stated"""


def build_user_content(notes: str) -> str:
    return (
        "Extract the action items from these notes.\n\n"
        + FEW_SHOT
        + "\n\n--- NOTES START ---\n"
        + notes
        + "\n--- NOTES END ---"
    )


def extract(client: genai.Client, notes: str):
    response = client.models.generate_content(
        model=MODEL,
        contents=build_user_content(notes),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0,
        ),
    )
    return response


def main() -> None:
    args = parse_args()
    client = make_client()
    notes = read_notes(args.notes_file)
    response = extract(client, notes)

    print("ACTION ITEMS\n------------")
    print(response.text)
    print("------------")
    usage = response.usage_metadata
    print(f"Prompt tokens:   {usage.prompt_token_count}")
    print(f"Response tokens: {usage.candidates_token_count}")
    print(f"Total tokens:    {usage.total_token_count}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print("Error: that notes file does not exist.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: the API call failed - {e}")
        sys.exit(1)
