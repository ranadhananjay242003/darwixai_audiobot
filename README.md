# 🎯 Darwix AI — Sales Call Intelligence Microservice

A production-grade, modular Python microservice for processing sales-call audio snippets. Built with **FastAPI**, **Whisper**, **HuggingFace Transformers**, and **SQLAlchemy** — designed for horizontal scalability, reliability, and extensibility.

---

## 📐 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (curl / frontend)                        │
└───────────────┬──────────────────┬──────────────────┬────────────────────┘
                │                  │                  │
        POST /transcribe    POST /speak        POST /replay
                │                  │                  │
┌───────────────▼──────────────────▼──────────────────▼────────────────────┐
│                          API LAYER (FastAPI)                              │
│               app/api/routes.py — HTTP handling only                     │
└───────┬──────────────────┬──────────────────┬──────────────────┬─────────┘
        │                  │                  │                  │
┌───────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐ ┌──────▼─────────┐
│  STT Service   │ │  TTS Service   │ │   Sentiment    │ │   Coachable    │
│  (Whisper)     │ │  (gTTS)        │ │   Service (HF) │ │   Detection    │
│                │ │                │ │                │ │   (Rule-based) │
└───────┬────────┘ └────────────────┘ └────────────────┘ └────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────────┐
│                    WORKER LAYER (app/workers/tasks.py)                    │
│             Orchestrates: STT → Sentiment → Coachable → Persist          │
│                     (Celery-ready task architecture)                      │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────────┐
│                       DATABASE LAYER (SQLAlchemy)                         │
│                                                                          │
│   ┌──────────┐    ┌──────────────┐    ┌──────────────────────────┐      │
│   │  calls   │───▶│ transcripts  │    │       segments           │      │
│   │          │───▶│              │    │  (speaker, sentiment,    │      │
│   │          │    │              │    │   coachable metadata)    │      │
│   └──────────┘    └──────────────┘    └──────────────────────────┘      │
│                                                                          │
│              SQLite (dev) ←→ PostgreSQL (prod) via env var               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
darwix/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory + lifecycle
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # Route definitions only (no logic)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic Settings (env-driven)
│   │   ├── exceptions.py          # Custom exception hierarchy
│   │   └── logging.py             # Structured JSON logging
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── session.py             # Engine + session factory
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py              # Pydantic request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stt_service.py         # Speech-to-Text (Whisper)
│   │   ├── tts_service.py         # Text-to-Speech (gTTS / pyttsx3)
│   │   ├── sentiment_service.py   # Sentiment analysis (HuggingFace)
│   │   └── coachable_service.py   # Coachable moment detection
│   └── workers/
│       ├── __init__.py
│       └── tasks.py               # Pipeline orchestration (Celery-ready)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures
│   ├── test_stt_service.py        # STT unit tests
│   ├── test_sentiment_service.py  # Sentiment unit tests
│   ├── test_coachable_service.py  # Coachable detection tests
│   └── test_api.py                # API integration tests
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD
├── .env.example                   # Environment variable template
├── .gitignore
├── Dockerfile                     # Multi-stage Docker build
├── docker-compose.yml             # Compose with optional Postgres/Redis
├── pyproject.toml                 # Tooling config
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── DESIGN_BRIEF.md                # Architectural decisions document
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **ffmpeg** (required by Whisper for audio processing)
- **Docker** (optional, for containerized deployment)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-org/darwix-ai.git
cd darwix-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env as needed

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build the image
docker build -t darwix-ai .

# Run the container
docker run -p 8000:8000 darwix-ai

# Or with Docker Compose
docker-compose up --build
```

---

## 📡 API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-21T00:00:00Z"
}
```

---

### POST `/transcribe` — Speech-to-Text with Analysis

Upload a sales-call audio file for transcription, sentiment analysis, and coachable moment detection.

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "audio=@call_recording.wav" \
  -F "call_id=CALL-001" \
  -F "agent_id=AGENT-42" \
  -F "customer_id=CUST-100"
```

**Response:**
```json
{
  "call_id": "CALL-001",
  "status": "completed",
  "transcript": "Hello, I'm interested in your product. That sounds great, but it's a bit too expensive for our budget.",
  "segments": [
    {
      "speaker": "speaker_0",
      "start_time": 0.0,
      "end_time": 3.5,
      "text": "Hello, I'm interested in your product.",
      "sentiment": "POSITIVE",
      "sentiment_score": 0.92,
      "is_coachable": true,
      "coachable_type": "buying_signal"
    },
    {
      "speaker": "speaker_1",
      "start_time": 4.0,
      "end_time": 8.2,
      "text": "That sounds great, but it's a bit too expensive for our budget.",
      "sentiment": "NEGATIVE",
      "sentiment_score": 0.87,
      "is_coachable": true,
      "coachable_type": "objection"
    }
  ],
  "duration_seconds": 8.2,
  "language": "en"
}
```

---

### POST `/speak` — Text-to-Speech

Convert text to an audio file.

```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "The customer expressed a price objection at the 4-second mark."}' \
  --output speech.mp3
```

**Response:** Audio file download (MP3/WAV)

---

### POST `/replay` — Coachable Moment Replay

Retrieve and replay coachable moments from a previously transcribed call.

```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"call_id": "CALL-001"}' \
  --output replay.mp3
```

**Response:** Audio file containing TTS replay of coachable segments

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./darwix.db` | Database connection string. Use `postgresql://...` for production |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `TTS_PROVIDER` | `gtts` | TTS engine: `gtts` or `pyttsx3` |
| `SENTIMENT_ENABLED` | `true` | Enable/disable sentiment analysis |
| `SENTIMENT_MODEL` | `distilbert-base-uncased-finetuned-sst-2-english` | HuggingFace sentiment model |
| `COACHABLE_CONFIDENCE_THRESHOLD` | `0.5` | Minimum confidence for coachable detection |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum upload file size |
| `DB_POOL_SIZE` | `5` | Database connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Max overflow connections |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_coachable_service.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

---

## 📊 Scalability Strategy

### Horizontal Scaling

1. **Stateless API**: No in-memory state; all data persists in the database. Any instance can handle any request.
2. **Connection Pooling**: SQLAlchemy pool with `pre_ping` for connection health checks.
3. **Worker Isolation**: Heavy ML inference (STT, Sentiment) is isolated in the worker layer, ready for Celery migration.
4. **Load Balancing**: Run multiple uvicorn workers or deploy behind nginx/Traefik.

### Production Scaling Path

```
                    ┌──────────────┐
                    │  Load        │
                    │  Balancer    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌─────▼────┐ ┌─────▼────┐
        │ API Pod  │ │ API Pod  │ │ API Pod  │
        │ (Fast)   │ │ (Fast)   │ │ (Fast)   │
        └─────┬────┘ └─────┬────┘ └─────┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │   Message    │
                    │   Queue      │
                    │ (RabbitMQ)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌─────▼────┐ ┌─────▼────┐
        │ Worker   │ │ Worker   │ │ Worker   │
        │ (STT+ML) │ │ (STT+ML) │ │ (STT+ML) │
        │ (GPU)    │ │ (GPU)    │ │ (GPU)    │
        └──────────┘ └──────────┘ └──────────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL  │
                    │  (Primary +  │
                    │   Replicas)  │
                    └──────────────┘
```

---

## 🔄 Trade-offs

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| SQLite default | Not production-scale | Zero-config for development; PostgreSQL switchable via env |
| Pseudo-diarization | Not true speaker separation | Whisper timestamps + gap detection; pyannote can be plugged in |
| Rule-based coachable detection | Less accurate than ML | Fast, deterministic, explainable; NLP classifier ready to swap in |
| Synchronous processing | Blocks on large files | Celery integration designed but not wired; MVP simplicity |
| gTTS | Requires internet | Free, reliable; swap to pyttsx3 or Coqui for offline |

---

## 🔮 Future Improvements

- [ ] **True Speaker Diarization**: Integrate pyannote-audio for real speaker identification
- [ ] **Celery Workers**: Full async pipeline with RabbitMQ/Redis
- [ ] **ML Coachable Classifier**: Fine-tuned BERT model for coachable moment classification
- [ ] **Streaming STT**: Real-time transcription via WebSocket
- [ ] **Call Analytics Dashboard**: Frontend for reviewing calls and coaching insights
- [ ] **Multi-language Support**: Extend sentiment and coachable detection beyond English
- [ ] **Object Storage**: Move audio files to S3/MinIO for distributed deployments
- [ ] **Rate Limiting**: API rate limiting for multi-tenant usage
- [ ] **OpenTelemetry**: Distributed tracing for observability
- [ ] **Alembic Migrations**: Database schema versioning

---

## 📄 Interactive API Docs

Once running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.
