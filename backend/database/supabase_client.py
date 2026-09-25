import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# Server-side only; never ship service_role to the browser
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


def user_client(access_token: str) -> Client:
    """Supabase client scoped to a user JWT so RLS sees auth.uid()."""
    client = create_client(supabase_url, supabase_key)
    client.postgrest.auth(access_token)
    return client
