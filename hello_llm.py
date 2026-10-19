import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model=MODEL,
    contents="Explain tokens in two sentences, for a data engineer.",
)

print(response.text)
print("---")
usage = response.usage_metadata
print(f"Prompt tokens:   {usage.prompt_token_count}")
print(f"Response tokens: {usage.candidates_token_count}")
print(f"Total tokens:    {usage.total_token_count}")
