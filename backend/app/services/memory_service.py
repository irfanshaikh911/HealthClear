"""
Memory Service — saves/loads conversation history to Supabase chat_history table.
"""
from datetime import datetime, timezone
from typing import Optional

from supabase import Client


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string for Supabase."""
    return datetime.now(timezone.utc).isoformat()


def init_history(client: Client, session_id: str, patient_id: Optional[int] = None) -> None:
    """Create a new chat_history row for this session."""
    client.table("chat_history").upsert(
        {
            "session_id": session_id,
            "patient_id": patient_id,
            "messages": [],
            "answers": {},
            "result": None,
            "updated_at": _now_iso(),
        },
        on_conflict="session_id",
    ).execute()


def append_message(client: Client, session_id: str, role: str, content: str) -> None:
    """Append a {role, content} message to chat_history.messages JSONB array."""
    try:
        row = (
            client.table("chat_history")
            .select("messages")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        messages: list = (row.data or {}).get("messages", [])
        messages.append({"role": role, "content": content, "ts": _now_iso()})

        client.table("chat_history").update(
            {"messages": messages, "updated_at": _now_iso()}
        ).eq("session_id", session_id).execute()
    except Exception:
        pass


def save_answers(client: Client, session_id: str, answers: dict) -> None:
    """Persist the current collected answers snapshot to Supabase."""
    try:
        serializable = {}
        for k, v in answers.items():
            if isinstance(v, (str, int, float, bool, list, type(None))):
                serializable[k] = v
            else:
                serializable[k] = str(v)

        client.table("chat_history").update(
            {"answers": serializable, "updated_at": _now_iso()}
        ).eq("session_id", session_id).execute()
    except Exception:
        pass


def save_result(client: Client, session_id: str, result_payload: dict) -> None:
    """Persist the final cost estimation result JSON to Supabase."""
    try:
        client.table("chat_history").update(
            {"result": result_payload, "updated_at": _now_iso()}
        ).eq("session_id", session_id).execute()
    except Exception:
        pass


def load_history(client: Client, session_id: str) -> Optional[dict]:
    """Load the full history dict for a session from Supabase."""
    try:
        row = (
            client.table("chat_history")
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        return row.data if row.data else None
    except Exception:
        return None


def get_all_sessions(client: Client, patient_id: int) -> list:
    """Return all past sessions for a given patient_id, newest first."""
    try:
        rows = (
            client.table("chat_history")
            .select("session_id,answers,result,created_at,updated_at")
            .eq("patient_id", patient_id)
            .order("created_at", desc=True)
            .execute()
        )
        return rows.data or []
    except Exception:
        return []
