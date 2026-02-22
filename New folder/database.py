import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase environment variables (URL & KEY) must be set in your .env file."
    )

_supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db() -> Client:
    """FastAPI dependency — returns the shared Supabase client."""
    return _supabase_client
