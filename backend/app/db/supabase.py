"""Supabase client initialisation and FastAPI dependency."""

from supabase import create_client, Client

from app.core.config import settings

supabase: Client = create_client(
    settings.PUBLIC_SUPABASE_URL,
    settings.PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY,
)


def get_supabase() -> Client:
    """FastAPI dependency that provides the Supabase client."""
    return supabase
