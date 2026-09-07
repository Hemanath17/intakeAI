import json
import os
import time
from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()
# MODEL_NAME = "llama-3.3-70b-versatile"
MODEL_NAME = "openai/gpt-oss-120b"
# MODEL_NAME = "openai/gpt-oss-20b"
MAX_RETRIES = 3
client = Groq()

def generate_text(prompt: str, system: str = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(model=MODEL_NAME, messages=messages)
            return response.choices[0].message.content
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(3 * (attempt + 1))

def generate_json(prompt: str, system: str = None) -> dict:
    combined_text = (system or "") + prompt
    if "json" not in combined_text.lower():
        raise ValueError("Prompt must mention JSON when using generate_json")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(3 * (attempt + 1))
