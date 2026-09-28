"""qf_script: topic -> hook + scene plan. Key-optional (template fallback)."""

from __future__ import annotations

import json
import os

from pydantic import BaseModel, Field


class Scene(BaseModel):
    title: str
    voiceover: str
    caption: str
    visual_prompt: str
    duration_s: float = 2.5


class Script(BaseModel):
    topic: str
    hook: str
    scenes: list[Scene] = Field(min_length=3, max_length=3)
    hashtags: list[str] = []


def _punch(topic: str) -> str:
    """Topic core as 2-4 punchy caps words (filler stripped)."""
    filler = {"through", "the", "a", "an", "in", "on", "of", "and", "to"}
    words = [w for w in topic.strip().split() if w.lower() not in filler][:4]
    return " ".join(words).upper() or "QONEQT"


def template_script(topic: str) -> Script:
    t = topic.strip() or "Untitled community story"
    return Script(
        topic=t,
        hook=f"{t} — in 8 seconds, here's why it matters.",
        scenes=[
            Scene(
                title="The Hook",
                voiceover=f"Everyone scrolls past {t}. Here's the one thing worth stopping for.",
                caption="STOP SCROLLING",
                visual_prompt=f"{t}, dramatic cinematic still, hook moment",
            ),
            Scene(
                title="The Story",
                voiceover=f"Communities on Qoneqt are talking about {t} — three takes, one thread.",
                caption=_punch(t),
                visual_prompt=f"{t}, vivid scene with people, photorealistic",
            ),
            Scene(
                title="The CTA",
                voiceover="Join the thread on Qoneqt. Post your take and tag it.",
                caption="POST IT ON QONEQT",
                visual_prompt=f"celebration, {t}, confetti energy, cinematic",
            ),
        ],
        hashtags=["#Qoneqt", "#CtrlFreak"],
    )


def _try_openai(topic: str) -> Script | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        import httpx

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        prompt = (
            "You write short vertical-video scripts for the Qoneqt Global Feed. "
            f"Topic: {topic}. Return JSON with hook, 3 scenes, hashtags. "
            "Keep voiceover under 25 words per scene. No markdown, JSON only."
        )
        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        data = json.loads(text[text.index("{") : text.rindex("}") + 1])
        scenes = [Scene(**s) for s in data["scenes"][:3]]
        return Script(topic=topic, hook=data.get("hook", ""), scenes=scenes, hashtags=data.get("hashtags", []))
    except Exception:
        return None


def _try_groq(topic: str) -> Script | None:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return None
    try:
        import httpx

        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        prompt = (
            "You write short vertical-video scripts for the Qoneqt Global Feed. "
            f"Topic: {topic}. Return JSON with hook, 3 scenes, hashtags. "
            "Keep voiceover under 25 words per scene. No markdown, JSON only."
        )
        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        data = json.loads(text[text.index("{") : text.rindex("}") + 1])
        scenes = [Scene(**s) for s in data["scenes"][:3]]
        return Script(topic=topic, hook=data.get("hook", ""), scenes=scenes, hashtags=data.get("hashtags", []))
    except Exception:
        return None


def generate_script(topic: str) -> Script:
    """Provider chain: OpenAI -> Groq -> deterministic template. Never raises on LLM failure."""
    return _try_openai(topic) or _try_groq(topic) or template_script(topic)
