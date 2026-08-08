"""Persona voice, style, tone, and editorial stance definitions."""

from __future__ import annotations

from typing import Any


def build_voice_config(name: str, domain: str) -> dict[str, Any]:
    """Build voice configuration dict matching the persona name and domain."""
    return {
        "name": name,
        "domain": domain,
        "tone": "analytical",
        "style": "incisive",
        "perspective": f"Expert analyst focused on {domain}",
    }
