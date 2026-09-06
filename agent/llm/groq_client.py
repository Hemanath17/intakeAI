import json
import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
MODEL_NAME = "llama-3.3-70b-versatile"
client = Groq()

def generate_text(prompt: str, system: str = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )
    return response.choices[0].message.content

def generate_json(prompt: str, system: str = None) -> dict:
    combined_text = (system or "") + prompt
    if "json" not in combined_text.lower():
        raise ValueError("Prompt must mention JSON when using generate_json")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content
    return json.loads(raw_content)