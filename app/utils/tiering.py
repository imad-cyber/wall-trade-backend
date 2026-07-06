"""Subscription tier helpers for field gating."""
from typing import Any, Optional

PRO_TIERS = frozenset({"pro", "institutional"})


def get_user_tier(user: Optional[dict[str, Any]]) -> str:
    if not user:
        return "free"
    tier = user.get("subscription_tier") or user.get("tier") or "free"
    return str(tier).lower()


def is_pro_user(user: Optional[dict[str, Any]]) -> bool:
    return get_user_tier(user) in PRO_TIERS


def apply_pro_lock(items: list[dict], *, tier: str, pro_key: str = "pro") -> list[dict]:
    if tier in PRO_TIERS:
        return items
    locked: list[dict] = []
    for item in items:
        if item.get(pro_key):
            locked.append({**item, "value": None, "locked": True})
        else:
            locked.append(item)
    return locked
