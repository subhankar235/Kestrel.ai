"""Persona voice, style, tone, and editorial stance definitions."""

from __future__ import annotations

from typing import Any


def build_voice_config(name: str, domain: str) -> dict[str, Any]:
    """Build comprehensive voice configuration matching persona name and domain."""
    domain_lower = domain.lower()
    
    if "security" in domain_lower or "cyber" in domain_lower:
        tone = "sharp, rigorous, security-minded"
        stance = "Skeptic of hype, focused on practical vulnerability analysis and evidence"
    elif "crypto" in domain_lower or "blockchain" in domain_lower:
        tone = "analytical, protocol-focused"
        stance = "Decentralization advocate, critical of centralized security flaws"
    elif "ai" in domain_lower or "machine learning" in domain_lower:
        tone = "incisive, technical, forward-looking"
        stance = "Pessimistic on AI safety claims, optimistic on developer empowerment"
    else:
        tone = "analytical, objective, concise"
        stance = f"Domain expert focused on {domain}"

    return {
        "name": name,
        "domain": domain,
        "tone": tone,
        "stance": stance,
        "vocabulary_rules": ["avoid marketing buzzwords", "use precise technical terminology"],
        "max_post_length": 500,
    }
