
import threading
from fastapi.responses import StreamingResponse

def keepalive_json(work):
    """Run work() in a thread and send spaces while waiting, so Cloudflare's
    ~100s limit never triggers. Leading spaces are ignored by response.json()."""
    def gen():
        box = {}
        def run():
            try:
                box["r"] = work()
            except Exception as e:
                box["r"] = {"success": False, "error": str(e)}
        t = threading.Thread(target=run, daemon=True)
        t.start()
        while t.is_alive():
            yield b" "
            t.join(timeout=10)
        yield json.dumps(box["r"]).encode("utf-8")
    return StreamingResponse(gen(), media_type="application/json")

from fastapi import FastAPI
import urllib.request
import json

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="IIUC ResearchMatch")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)



@app.get("/", include_in_schema=False)
def serve_homepage():
    return FileResponse(STATIC_DIR / "index.html")

OLLAMA_URL = "http://localhost:11434/api/tags"
MODEL_NAME = "gemma4:e4b"




@app.get("/api/health")
def health():
    try:
        request = urllib.request.Request(OLLAMA_URL)

        with urllib.request.urlopen(
            request, timeout=5
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        models = [
            model["name"]
            for model in data.get("models", [])
        ]

        model_available = any(
            name == MODEL_NAME
            or name.startswith(MODEL_NAME + ":")
            for name in models
        )

        return {
            "backend": "ok",
            "ollama": "connected",
            "model": MODEL_NAME,
            "model_available": model_available
        }

    except Exception as error:
        return {
            "backend": "ok",
            "ollama": "unavailable",
            "error": str(error)
        }



from pydantic import BaseModel


class ResearchInput(BaseModel):
    text: str


@app.post("/api/analyze")
def analyze_research(data: ResearchInput):
    prompt = f"""
Analyze the following student research idea.

Return only valid JSON with these fields:
- research_topic: a short research topic
- methods: a list of possible research methods mentioned or implied
- skills: a list of relevant technical skills
- keywords: a list of important search keywords

Do not invent specific facts about the research.
If information is missing, return an empty list for that field.

Student research idea:
{data.text}
"""

    try:
        request_data = json.dumps({
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0}
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(
            request, timeout=300
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        extracted = json.loads(result["response"])

        return {
            "success": True,
            "analysis": extracted
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }



# Load the demonstration faculty profiles
FACULTY_FILE = Path(__file__).parent / "faculty.json"


def profile_to_text(profile):
    parts = (
        profile.get("research_areas", [])
        + profile.get("methods", [])
        + profile.get("keywords", [])
    )
    return " ".join(parts)


@app.post("/api/match")
def match_faculty(data: ResearchInput):
    try:
        with open(FACULTY_FILE, "r", encoding="utf-8") as file:
            faculty = json.load(file)

        if not data.text.strip():
            return {"success": False, "error": "Enter a research idea."}

        profile_texts = [
            profile_to_text(profile) for profile in faculty
        ]

        vectorizer = TfidfVectorizer()
        all_texts = profile_texts + [data.text]
        vectors = vectorizer.fit_transform(all_texts)

        scores = cosine_similarity(
            vectors[-1], vectors[:-1]
        ).flatten()

        results = []

        for index, profile in enumerate(faculty):
            student_words = set(
                data.text.lower().replace("-", " ").split()
            )
            profile_words = set(
                profile_to_text(profile).lower()
                .replace("-", " ").replace(",", " ").split()
            )

            shared_terms = sorted(
                word for word in student_words & profile_words
                if len(word) > 2
            )

            results.append({
                "name": profile["name"],
                "department": profile["department"],
                "research_areas": profile["research_areas"],
                "similarity_score": round(
                    float(scores[index]) * 100, 2
                ),
                "shared_terms": shared_terms
            })

        results.sort(
            key=lambda item: item["similarity_score"],
            reverse=True
        )

        return {
            "success": True,
            "demo_data": True,
            "matches": results
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }



class ChatInput(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/api/chat")
def research_chat(data: ChatInput):
    message = data.message.strip()

    if not message:
        return {"success": False, "error": "Please enter a message."}

    # Keep only recent conversation messages.
    conversation = data.history[-10:]

    messages = [
        {
            "role": "system",
            "content": (
                "You are the IIUC ResearchMatch research assistant. "
                "Help university students understand research topics, "
                "identify the skills they need, plan beginner-friendly "
                "learning roadmaps, explore project ideas, and understand "
                "research methods. Explain technical concepts clearly. "
                "Ask a follow-up question when it would help. "
                "Do not claim that fictional faculty profiles are real. "
                "Do not invent research papers, citations, faculty details, "
                "or learning resources. Distinguish suggestions from facts. "
                "Give practical steps appropriate for a beginner."
            )
        }
    ]

    for item in conversation:
        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and isinstance(content, str):
            if content.strip():
                messages.append({
                    "role": role,
                    "content": content[:4000]
                })

    messages.append({"role": "user", "content": message})

    try:
        request_data = json.dumps({
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4}
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result.get("message", {}).get("content", "").strip()

        if not answer:
            return {
                "success": False,
                "error": "The local model returned an empty answer."
            }

        return {"success": True, "answer": answer}

    except Exception as error:
        return {"success": False, "error": str(error)}
