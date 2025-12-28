# 🎥 Scalable Video Streaming Backend

A production-ready, containerized video streaming infrastructure built with Python (FastAPI), Celery, and FFmpeg. This system handles video ingestion, asynchronous transcoding to Adaptive Bitrate (ABR) HLS format, and scalable delivery using Object Storage.

## 🚀 Features

- **Scalable Architecture**: Dockerized microservices (API, Worker, Redis, Postgres, MinIO).
- **Asynchronous Transcoding**: Offloads heavy video processing to background Celery workers.
- **Adaptive Bitrate Streaming (ABR)**: Automatically generates 1080p, 720p, and 360p HLS playlists for optimal playback on any device.
- **HLS Standard**: Uses HTTP Live Streaming (.m3u8 + .ts) for broad compatibility.
- **Object Storage**: Cloud-agnostic storage layer (MinIO for local, AWS S3 for production).
- **Observability**: Built-in health checks and system statistics endpoints.

## 🛠️ Tech Stack

- **Language**: Python 3.11
- **API Framework**: FastAPI
- **Task Queue**: Celery
- **Broker**: Redis
- **Database**: PostgreSQL (Metadata & Job Status)
- **Object Storage**: MinIO (S3 Compatible)
- **Transcoding**: FFmpeg (with `libx264` and `aac`)
- **Infrastructure**: Docker & Docker Compose

## 🏗️ Architecture

```mermaid
graph TD
    Client[Client] -->|1. Upload Video| API[FastAPI Service]
    API -->|2. Save Raw File| S3[MinIO/S3 Storage]
    API -->|3. Create Job| DB[(PostgreSQL)]
    API -->|4. Queue Task| Redis[Redis Broker]
    
    Worker[Celery Worker] -->|5. Consume Task| Redis
    Worker -->|6. Fetch Raw File| S3
    Worker -->|7. Transcode (FFmpeg)| Worker
    Worker -->|8. Upload HLS Segments| S3
    Worker -->|9. Update Status| DB
    
    Client -->|10. Request Stream| API
    API -->|11. Proxy/Redirect| S3
```

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for running local tests)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd streamer
   ```

2. **Start Services**
   ```bash
   docker compose up --build -d
   ```
   *This starts the API (port 8000), Worker, Postgres (5433), Redis (6389), and MinIO (9005).*

3. **Run Migrations**
   ```bash
   # Run alembic migrations strictly inside the container to avoid env issues
   docker compose exec web alembic upgrade head
   ```

4. **Verify Deployment**
   ```bash
   curl http://localhost:8000/api/v1/system/health
   # Expected: {"status": "healthy", ...}
   ```

## 📖 API Documentation

The interactive API documentation (Swagger UI) is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Core Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/videos/upload` | Upload a video file (multipart/form-data). |
| `GET` | `/api/v1/videos/{job_id}` | Check processing status (queued, processing, completed). |
| `GET` | `/stream/job/{job_id}` | Get the master HLS playlist (.m3u8). |
| `GET` | `/api/v1/system/stats` | View system job statistics. |

## 🧪 Testing

We have a built-in verification script that generates a test video, uploads it, waits for processing, and verifies the HLS stream.

1. **Install Test Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Verification Script**
   ```bash
   python tests/verify.py
   ```

## 🔧 Configuration

Configuration is managed via environment variables (see `.env` or `docker-compose.yml`).

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Postgres connection string | `postgresql://...` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://redis:6379/0` |
| `S3_ENDPOINT_URL` | MinIO/S3 API URL | `http://minio:9000` |
| `Initial_BUCKET_NAME` | Bucket for storage | `videos` |

## 🤝 Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up a local development environment and submit pull requests.
