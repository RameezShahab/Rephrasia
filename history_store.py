"""
history_store.py — In-memory history storage for tracking AI operations.

Provides CRUD operations for user activity history.
In production, swap _history_db for a real database (SQLite/PostgreSQL).

Each history item is scoped to a user_id so that multi-user environments
return only the current user's history.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── In-Memory Store ───────────────────────────────────────────────────────────
# Key: user_id → list of history items
_history_db: Dict[str, List[dict]] = {}

# ── Global Stats Counters ─────────────────────────────────────────────────────
_stats: Dict[str, int] = {
    "words_generated": 0,
    "documents_created": 0,
    "ai_requests": 0,
}


# ── History CRUD ──────────────────────────────────────────────────────────────

def record_activity(
    user_id: str,
    title: str,
    activity_type: str,
    word_count: int = 0,
) -> dict:
    """
    Record a new activity in the user's history.

    Args:
        user_id:       Owner of this history item.
        title:         Human-readable description (e.g. "Paraphrased Blog Article").
        activity_type: One of 'Paraphraser', 'Translator', 'Grammar Checker', 'AI Chat'.
        word_count:    Number of words generated (for stats tracking).

    Returns:
        The newly created history item dict.
    """
    item = {
        "id": uuid.uuid4().hex,
        "title": title,
        "type": activity_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _history_db.setdefault(user_id, []).insert(0, item)  # Newest first

    # Update global stats
    _stats["ai_requests"] += 1
    _stats["words_generated"] += word_count
    if activity_type in ("Paraphraser", "Translator"):
        _stats["documents_created"] += 1

    logger.debug("Recorded activity for user %s: %s", user_id, title)
    return item


def list_history(
    user_id: str,
    search: Optional[str] = None,
    activity_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[List[dict], int]:
    """
    List history items for a user with optional filtering and pagination.

    Returns:
        (paginated_items, total_matching_count)
    """
    items = _history_db.get(user_id, [])

    # Filter
    if search:
        search_lower = search.lower()
        items = [i for i in items if search_lower in i["title"].lower()]
    if activity_type:
        items = [i for i in items if i["type"].lower() == activity_type.lower()]

    total = len(items)

    # Paginate
    start = (page - 1) * limit
    end = start + limit
    paginated = items[start:end]

    # Add relative time strings
    now = datetime.now(timezone.utc)
    for item in paginated:
        created = datetime.fromisoformat(item["created_at"])
        item["time"] = _relative_time(now, created)

    return paginated, total


def delete_history_item(user_id: str, item_id: str) -> bool:
    """
    Delete a specific history item.

    Returns:
        True if deleted, False if not found.
    """
    items = _history_db.get(user_id, [])
    for i, item in enumerate(items):
        if item["id"] == item_id:
            items.pop(i)
            logger.debug("Deleted history item %s for user %s", item_id, user_id)
            return True
    return False


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats(user_id: str) -> dict:
    """
    Get dashboard statistics for a user.

    Currently returns global stats (all users combined).
    In production, scope these counters per user.
    """
    # Get recent activity for the user
    items = _history_db.get(user_id, [])[:5]
    now = datetime.now(timezone.utc)

    recent = []
    for item in items:
        created = datetime.fromisoformat(item["created_at"])
        recent.append({
            "title": item["title"],
            "time": _relative_time(now, created),
        })

    return {
        "words_generated": _stats["words_generated"],
        "documents_created": _stats["documents_created"],
        "ai_requests": _stats["ai_requests"],
        "weekly_usage": _compute_weekly_usage(user_id),
        "recent_activity": recent,
    }


def _compute_weekly_usage(user_id: str) -> List[int]:
    """
    Compute a 7-day activity histogram for the user.

    Returns a list of 7 integers representing daily request counts
    from 6 days ago through today.
    """
    items = _history_db.get(user_id, [])
    now = datetime.now(timezone.utc)
    counts = [0] * 7

    for item in items:
        created = datetime.fromisoformat(item["created_at"])
        delta = (now - created).days
        if 0 <= delta < 7:
            counts[6 - delta] += 1  # Index 6 = today

    return counts


def _relative_time(now: datetime, then: datetime) -> str:
    """Convert a datetime to a human-readable relative time string."""
    delta = now - then
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = seconds // 60
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h ago"
    elif seconds < 172800:
        return "Yesterday"
    else:
        days = seconds // 86400
        return f"{days} days ago"
