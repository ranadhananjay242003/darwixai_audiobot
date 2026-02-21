# 📘 Design Brief — Darwix AI Sales Call Intelligence

## Architectural Decisions

### Clean Architecture & Separation of Concerns

The system follows a strict layered architecture:

1. **API Layer** (`app/api/`): Handles HTTP concerns only — request parsing, response formatting, status codes. Contains zero business logic.
2. **Service Layer** (`app/services/`): Each ML/AI capability (STT, TTS, Sentiment, Coachable Detection) is an independent, testable module with its own interface.
3. **Worker Layer** (`app/workers/`): Orchestrates multi-step pipelines. Designed as a Celery task body — the transition from synchronous to async is a configuration change, not a rewrite.
4. **Database Layer** (`app/db/`): ORM models and session management, injected into API routes via FastAPI's `Depends()`.

**Why modular design?** Each service can be:
- Tested independently with mocks
- Replaced (e.g., swap Whisper for AWS Transcribe) without touching other layers
- Scaled separately (GPU workers for STT, CPU for coachable detection)

### Horizontal Scalability

The system is **stateless by design**:
- No in-memory caches or session state
- All data flows through the database
- Audio files stored on disk (or object storage in production)
- Any API instance can serve any request

**Scaling strategy:**
- **Phase 1 (current)**: Single process, SQLite, synchronous
- **Phase 2**: Multiple uvicorn workers, PostgreSQL, add DB pool tuning
- **Phase 3**: Celery workers for STT/ML, RabbitMQ broker, GPU worker nodes
- **Phase 4**: Kubernetes deployment, HPA on API pods, GPU node pools for workers

### Fault Tolerance Strategy

1. **Graceful degradation**: Sentiment analysis failure doesn't block transcription. Coachable detection failure doesn't block the response.
2. **Structured error hierarchy**: `DarwixBaseError` → typed exceptions → mapped HTTP status codes. No raw `Exception` leaks to the client.
3. **Retry design**: Worker tasks use `try/except` with status tracking (`pending → processing → completed | failed`). In Celery, this maps to `max_retries=3` with exponential backoff.
4. **Monitoring**: JSON-structured logging with timestamps, module names, and exception traces — ready for ELK/Datadog/CloudWatch ingestion.

**Backlog handling:**
- Overloaded system → requests queue in the message broker
- Workers autoscale based on queue depth
- API returns `202 Accepted` with a polling endpoint (future)
- Dead letter queue for permanently failed tasks

### Trade-offs Made for MVP

| Area | Decision | Production path |
|------|----------|-----------------|
| Diarization | Gap-based speaker alternation | Integrate pyannote-audio or cloud diarization API |
| Coachable detection | Regex patterns + sentiment boost | Fine-tune a DistilBERT classifier on labeled sales data |
| Task processing | Synchronous in request cycle | Celery with Redis/RabbitMQ broker |
| Database | SQLite with WAL mode | PostgreSQL with read replicas |
| TTS | gTTS (network-dependent) | Self-hosted Coqui TTS or ElevenLabs API |
| Auth | None | JWT/OAuth2 with FastAPI Security |

### Extensibility Plan

The architecture supports extension without modification (Open/Closed Principle):

1. **New STT provider**: Implement `transcribe(audio_path) → TranscriptionResult` interface
2. **New coachable category**: Add regex patterns to the pattern list, or plug in an ML classifier
3. **New API endpoint**: Add route in `app/api/`, delegate to a new or existing service
4. **New database**: Change `DATABASE_URL` in `.env`; add Alembic for migrations
5. **Real-time processing**: Add WebSocket endpoint that streams to STT service
6. **Multi-tenant**: Add tenant_id to models, scope queries, add auth middleware

The goal: **every change is additive, not surgical.**

---

*Document version: 1.0 | Last updated: 2026-02-21*
