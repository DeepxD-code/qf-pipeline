from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    storage_dir: str = "storage"
    secs_per_image: float = 2.5
    # Visual backend: "cards" (Pillow, offline, default) or "hyperframes" (motion HTML -> MP4).
    # Per skills/heygen-hyperframes/SKILL.md: HTML composition for promo/explainer.
    qf_visuals: str = "cards"
    # Composer: "python" (subprocess ffmpeg) or "java" (workers/java-renderer, bounded CPU).
    qf_composer: str = "python"
    # Voiceover: "1" = free Edge-TTS narration muxed under the video (silent fallback).
    qf_voice: str = "1"
    # Bound concurrent renders so a burst of topics can't melt the box.
    max_concurrent_renders: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
