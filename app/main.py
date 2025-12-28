from fastapi import FastAPI
from app.core.config import settings
from app.api.endpoints import videos, stream, system

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def read_root():
    return {"message": "Video Streamer API is running"}

app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
