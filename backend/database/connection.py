"""
Supabase database connection.
"""

import os
from supabase import create_client, Client


def get_supabase() -> Client:
    """Get Supabase client instance."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables. "
            "Check your .env file."
        )

    return create_client(url, key)
