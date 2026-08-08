"""Phase 5 — health endpoint integration test."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}