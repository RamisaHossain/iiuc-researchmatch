
import base64
import json
import urllib.request
import urllib.error
from pathlib import Path

MODEL = "gemma4:e4b"
URL = "http://localhost:11434/api/generate"

image_path = input("Enter the full image path: ").strip().strip('"')

path = Path(image_path)

if not path.is_file():
    print("ERROR: Image file not found.")
    raise SystemExit(1)

with path.open("rb") as image_file:
    image_data = base64.b64encode(
        image_file.read()
    ).decode("utf-8")

prompt = """
Examine this image for research-related information.

Return one JSON object with these fields:
{
  "status": "OK or UNCLEAR",
  "research_topic": "",
  "methods": [],
  "skills": [],
  "keywords": [],
  "reason": ""
}

Use status OK only if you can identify meaningful
research information from the image.

If the image is blank, unreadable, or contains no
identifiable research idea, use status UNCLEAR.
Do not invent missing information.
Return only valid JSON.
"""

payload = {
    "model": MODEL,
    "prompt": prompt,
    "images": [image_data],
    "stream": False,
    "format": "json",
    "options": {
        "temperature": 0
    }
}

request = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))

    print("\n--- GEMMA RESPONSE ---")
    print(result.get("response", "No response returned."))

except urllib.error.URLError as error:
    print("Could not connect to Ollama.")
    print("Check that Ollama is running.")
    print(error)

except TimeoutError:
    print("The request timed out. Try a smaller image.")

except Exception as error:
    print("Test failed:", error)
