# Darwix AI - Sales Intelligence Microservice

A production-grade microservice for processing sales-call audio, identifying coachable moments, and generating AI-driven insights.

## 🚀 Quick Start (Docker)

The easiest way to run the entire system (Backend + Premium Dashboard) is via Docker Compose:

```bash
docker-compose up --build
```

*   **Dashboard**: http://localhost:3000
*   **API Docs**: http://localhost:8000/docs

---

## 🛠️ Local Development Setup

1.  **Clone & Setup Environment**:
    ```bash
    git clone https://github.com/ranadhananjay242003/darwixai_audiobot.git
    cd darwixai_audiobot
    python -m venv venv
    ./venv/Scripts/activate  # or source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run Backend**:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

3.  **Run Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev -- --port 3000
    ```

---

## 🧪 Testing the Endpoints (CURL)

### 1. Transcribe Audio
Upload a call recording for AI analysis.
```bash
curl -X POST "http://localhost:8000/transcribe" \
     -H "Content-Type: multipart/form-data" \
     -F "audio=@tests/sample_call.wav" \
     -F "agent_id=AgentSmith" \
     -F "customer_id=Cust001"
```

### 2. Standard TTS
Convert text to an audio file.
```bash
curl -X POST "http://localhost:8000/speak" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, thank you for choosing Darwix AI."}' \
     --output speech.mp3
```

### 3. Replay Coachable Moments
Generate a synthesized audio recap of specific highlights from a previous call.
```bash
curl -X POST "http://localhost:8000/replay" \
     -H "Content-Type: application/json" \
     -d '{"call_id": "YOUR_CALL_ID_HERE"}' \
     --output replay.mp3
```

---

## 🏗️ Architecture Summary

*   **FastAPI**: Modern, high-performance API layer.
*   **OpenAI Whisper**: State-of-the-art Speech-to-Text.
*   **HuggingFace Transformers**: Sentiment analysis (DistilBERT).
*   **gTTS**: Reliable Text-to-Speech playback.
*   **SQLAlchemy + SQLite**: Robust local data persistence.
*   **React + Vite**: Sleek, high-performance sales dashboard.

For a deep dive into the engineering decisions, see **[DESIGN_BRIEF.md](./DESIGN_BRIEF.md)**.

---

## 🧪 Quality Assurance
Run the passing automated test suite (32 tests):
```bash
python -m pytest tests/ -v
```
