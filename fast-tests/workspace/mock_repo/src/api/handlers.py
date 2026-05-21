"""Route handlers for the mock API service."""

from src.api.database import DatabaseClient
from src.api.cache import get_cached, set_cached


def get_user(user_id: int):
    """Return a user record by ID."""
    db = DatabaseClient()
    return db.query("SELECT * FROM users WHERE id = %s", (user_id,))


def get_user_preferences(user_id: int):
    """Return stored preferences JSON blob for a user."""
    cached = get_cached(f"prefs:{user_id}")
    if cached is not None:
        return cached
    db = DatabaseClient()
    result = db.query("SELECT preferences FROM users WHERE id = %s", (user_id,))
    set_cached(f"prefs:{user_id}", result)
    return result


def update_user_preferences(user_id: int, preferences: dict):
    """Persist updated preferences for a user."""
    db = DatabaseClient()
    db.query(
        "UPDATE users SET preferences = %s WHERE id = %s",
        (preferences, user_id),
    )
    return {"status": "ok"}
