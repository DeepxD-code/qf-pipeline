from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    secs_per_image: float | None = Field(default=None, ge=1.0, le=6.0)


class Job(BaseModel):
    id: str
    topic: str
    status: str
    stage: str = ""
    script: dict | None = None
    video_url: str | None = None
    error: str | None = None
    created_at: str = ""
