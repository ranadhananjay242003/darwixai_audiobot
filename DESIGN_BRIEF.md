# Darwix AI: Design & Architecture Brief

## 1. Architectural Decisions
The Darwix AI microservice follows a **Service-Oriented Architecture (SOA)** with a focus on **Separation of Concerns**.

*   **API Layer (FastAPI)**: Handles validation, routing, and request/response lifecycle. It remains "thin," delegating all processing to specialized services.
*   **Service Layer**: Encapsulates the business logic for STT, TTS, Sentiment, and Coachable detection. This makes the system modular; for instance, the STT provider can be swapped from Whisper to Deepgram by updating just one class.
*   **Persistence Layer**: Uses SQLAlchemy ORM to decouple the business logic from the specific database implementation (SQLite for dev, PostgreSQL for prod).

## 2. Scalability Strategy
To handle "high reliability and real-time use cases," the architecture is designed for **Horizontal Scaling**:

*   **Stateless API**: The FastAPI layer is stateless and can be scaled behind a load balancer (Nginx/ALB).
*   **Task Queuing (Celery/Redis)**: Long-running audio processing (STT) is decoupled from the request-response cycle. While currently synchronous for MVP simplicity, the code is structured for an immediate transition to Celery workers.
*   **Database Partitioning**: The schema uses `call_id` as a primary index, allowing for future database sharding if the ingestion volume exceeds a single instance's capacity.

## 3. Fault Tolerance & Reliability
*   **Graceful Degradation**: If non-critical services (like Sentiment Analysis) fail, the system is designed to catch the exception and continue with the transcription rather than crashing the whole request.
*   **Structured Logging**: Every operation is logged with a common `call_id` to allow for distributed tracing and rapid debugging during outages.
*   **Safety Guards**: Integrated `static-ffmpeg` to ensure the environment has necessary audio binaries regardless of the host OS configuration.

## 4. Trade-offs & Decisions
*   **SQLite for MVP**: Chosen for the "24-hour timebox" to ensure Zero-Config setup for reviewers. SQLAlchemy makes the shift to PostgreSQL a simple configuration change.
*   **Heuristic Diarization**: Used a timestamp-gap based diarization (1.5s silence) as a lightweight, low-latency alternative to heavy clustering models like Pyannote, which require significantly more compute.
*   **Mocking in Tests**: Used extensive mocking for ML models in CI/CD to ensure the pipeline is fast (runs in < 1 minute) while still verifying API and logic integrity.
