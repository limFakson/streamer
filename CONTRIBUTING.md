# Contributing Guide

Thank you for your interest in contributing to the Video Streaming Backend! This document provides guidelines to help you get started.

## 💻 Development Setup

### 1. Environment
We recommend developing in a Linux/Unix environment. You will need:
- Docker Engine & Docker Compose
- Python 3.11+
- Git

### 2. Local Setup
1. **Fork and Clone** the repository.
2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run Infrastructure**:
   Use Docker Compose to run the dependency services (Redis, Postgres, MinIO) without necessarily running the app containers if you want to debug locally, or run everything in Docker.
   ```bash
   docker compose up -d db redis minio
   ```
4. **Environment Variables**:
   Create a `.env` file based on the config in `app/core/config.py` or `.env.example` if available.

## 🧪 Running Tests

### End-to-End Verification
The most reliable test is the integration test script:
```bash
python tests/verify.py
```
This script validates the entire lifecycle:
1. Generates a dummy video with audio.
2. Uploads it to the API.
3. Polls for completion.
4. Validates the HLS master playlist and variants.

### Code Style
- Follow **PEP 8** guidelines.
- Use type hints for function arguments and return values.
- Keep functions small and focused.

## 📝 Pull Request Process

1. **Create a Branch**: Use descriptive names (e.g., `feature/add-auth`, `fix/upload-timeout`).
2. **Commit Changes**: Write clear, concise commit messages.
3. **Verify**: Ensure `tests/verify.py` passes before submitting.
4. **Submit PR**: Describe your changes, the motivation, and any testing performed.

## ⚠️ Important Implementation Details

- **FFmpeg**: The worker container relies on `ffmpeg` being installed. If you modify the `Dockerfile`, ensure FFmpeg remains available.
- **Migration**: If you modify SQLAlchemy models in `app/db/models.py`, generate a new migration:
  ```bash
  alembic revision --autogenerate -m "description of change"
  alembic upgrade head
  ```

Thank you for building with us! 🚀
