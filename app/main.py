from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import videos, stream, system
import os

app = FastAPI(title=settings.PROJECT_NAME)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Video Streamer API is running"}

app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

# Serve Static Files (Frontend)
# Ensure the directory exists to avoid startup error
# Root is /app. app/main.py is /app/app/main.py
# We want /app/frontend.
# dirname(abspath(__file__)) -> /app/app
# dirname(dirname(abspath(__file__))) -> /app
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if not os.path.exists(frontend_path):
    os.makedirs(frontend_path)

app.mount("/web", StaticFiles(directory=frontend_path, html=True), name="frontend")
