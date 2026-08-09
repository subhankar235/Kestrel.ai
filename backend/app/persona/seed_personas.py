"""Example seed personas (e.g. Ada - AI Security) for agent initialization."""

from __future__ import annotations

from typing import Any

from app.persona.voice import build_voice_config

SEED_PERSONAS: dict[str, dict[str, Any]] = {
    "Ada": {
        "name": "Ada",
        "domain": "AI Security",
        "voice_config": build_voice_config("Ada", "AI Security"),
    },
    "Turing": {
        "name": "Turing",
        "domain": "Cryptography",
        "voice_config": build_voice_config("Turing", "Cryptography"),
    },
}


def get_seed_persona(name: str, domain: str) -> dict[str, Any]:
    """Retrieve existing seed persona or generate new persona definition dynamically."""
    if name in SEED_PERSONAS:
        return SEED_PERSONAS[name]
    return {
        "name": name,
        "domain": domain,
        "voice_config": build_voice_config(name, domain),
    }
