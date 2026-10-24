# IIUC ResearchMatch

AI-powered research assistance and researcher matching for university students.

## Features
- **AI Research Assistant:** Get guidance on research topics, skills, and learning roadmaps.
- **Research Idea Analysis:** Extract research topics, methods, skills, and keywords.
- **Researcher Matching:** Match research interests with profiles using TF-IDF and cosine similarity.

## Tech Stack
- Python, FastAPI
- HTML, CSS, JavaScript
- Ollama with Gemma 4 (`gemma4:e4b`)
- Scikit-learn

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/RamisaHossain/iiuc-researchmatch.git
   cd iiuc-researchmatch
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the AI model:
   ```bash
   ollama pull gemma4:e4b
   ```

4. Start the application:
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

5. Open `http://127.0.0.1:8000`.

## API Documentation

Visit `http://127.0.0.1:8000/docs` while the server is running.

## Note
- Researcher profiles are fictional demonstration data.
- AI features require Ollama and the configured model to be running.
- Hosted deployment requires a separately accessible AI backend.

## Author
Ramisa Hossain  
Department of Computer Science and Engineering  
International Islamic University Chittagong

## Repository
https://github.com/RamisaHossain/iiuc-researchmatch
