"""Makes the 'I AM LOST!' summary.

- No audio  -> returns SAMPLE content (flagged is_sample=True, the UI says so).
- With audio -> asks Gemini (needs GEMINI_API_KEY). NOT tested yet: no audio capture exists in the front.
"""
import base64
import copy
import json
from typing import List

import httpx
from pydantic import BaseModel, ValidationError

from .config import GEMINI_API_KEY, GEMINI_MODEL

SAMPLE = {
    "t": "Photosynthesis: the light reactions",
    "p": ("In the last five minutes your teacher explained how plants turn light into chemical energy. "
          "Chlorophyll in the thylakoid membranes absorbs light, which excites electrons and splits water, "
          "releasing oxygen. The energised electrons pass along a transport chain that pumps hydrogen ions "
          "across the membrane, and the resulting gradient drives ATP production. ATP and NADPH are the "
          "products, and both move on to the Calvin cycle, where CO\u2082 is built into sugar."),
    "steps": [
        ["Light hits chlorophyll", "Electrons gain energy."],
        ["Water is split", "Oxygen is released as a by-product."],
        ["Electrons travel the chain", "Hydrogen ions are pumped across the membrane."],
        ["ATP and NADPH form", "The stored energy is now portable."],
        ["Calvin cycle starts", "CO\u2082 is converted into glucose."],
    ],
    "root": "Photosynthesis",
    "nodes": ["Chlorophyll", "Water splitting", "ATP and NADPH", "Calvin cycle", "Light reactions"],
}


def sample_summary() -> dict:
    return copy.deepcopy(SAMPLE)


class AIError(Exception):
    """Raised when the AI call fails; the route turns it into HTTP 502."""


class _Summary(BaseModel):
    t: str
    p: str
    steps: List[List[str]]
    root: str
    nodes: List[str]


PROMPT = """You are helping a student who lost the thread during a live class.
The audio is roughly the last five minutes of the lesson. Listen, then answer in the SAME language the teacher speaks.
Return ONLY a JSON object with exactly these keys:
  "t": short title of what was just taught,
  "p": one clear paragraph (4-6 sentences) explaining it to a student who missed it,
  "steps": 3-7 ordered steps, each a 2-item array ["short heading", "one-sentence detail"],
  "root": the central concept (1-3 words),
  "nodes": 4-7 key concept labels (1-3 words each) linked to the root.
Do not invent content that was not said. If there is no intelligible lesson speech, return {"t":"No speech detected","p":"","steps":[],"root":"","nodes":[]}."""


async def gemini_summary(audio: bytes, mime: str) -> dict:
    if not GEMINI_API_KEY:
        raise AIError("AI is not configured (set GEMINI_API_KEY in backend/.env).")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(audio).decode("ascii")}},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json=body, headers={"x-goog-api-key": GEMINI_API_KEY})
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _Summary.model_validate(json.loads(text)).model_dump()
    except (httpx.HTTPError, KeyError, IndexError, ValueError, ValidationError) as exc:
        raise AIError(f"The AI service failed: {type(exc).__name__}") from exc
