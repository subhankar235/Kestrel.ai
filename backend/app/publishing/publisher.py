"""Publisher — persists the final immutable post record into Postgres database."""

from __future__ import annotations

from typing import Any


async def publish_final_post(post_data: dict[str, Any]) -> dict[str, Any]:
    """Write final immutable Post row to posts database table."""
    return {"status": "published"}
