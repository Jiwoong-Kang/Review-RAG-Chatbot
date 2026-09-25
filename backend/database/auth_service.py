import re

from supabase_auth.errors import AuthError

from .supabase_client import supabase, user_client

# Supabase Auth still needs an email under the hood; users only see username.
INTERNAL_EMAIL_DOMAIN = "users.local"
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _username_to_email(username: str) -> str:
    return f"{_normalize_username(username)}@{INTERNAL_EMAIL_DOMAIN}"


def _validate_username(username: str) -> str | None:
    if not USERNAME_RE.match(username or ""):
        return "Username must be 3–30 characters: letters, numbers, underscore only."
    return None


def _user_payload(user) -> dict:
    meta = getattr(user, "user_metadata", None) or {}
    if not isinstance(meta, dict):
        meta = {}
    username = meta.get("username") or ""
    if not username and getattr(user, "email", None):
        email = user.email or ""
        if email.endswith(f"@{INTERNAL_EMAIL_DOMAIN}"):
            username = email.split("@", 1)[0]
    return {
        "id": user.id,
        "username": username,
        "name": meta.get("display_name") or meta.get("name") or username,
    }


class AuthService:
    """Username/password auth via Supabase (synthetic internal email, no email UX)."""

    @staticmethod
    def sign_up(name: str, username: str, password: str) -> dict:
        try:
            username = _normalize_username(username)
            name = (name or "").strip()
            err = _validate_username(username)
            if err:
                return {"status": "error", "message": err}
            if not name:
                return {"status": "error", "message": "Name is required"}
            if len(password or "") < 6:
                return {"status": "error", "message": "Password must be at least 6 characters"}

            result = supabase.auth.sign_up({
                "email": _username_to_email(username),
                "password": password,
                "options": {
                    "data": {
                        "display_name": name,
                        "username": username,
                    }
                },
            })
            session = result.session
            user = result.user
            if not user:
                return {"status": "error", "message": "Sign up failed"}
            if not session:
                return {
                    "status": "error",
                    "message": (
                        "Account was created but no session was returned. "
                        "In Supabase Authentication settings, disable Confirm email, "
                        "then delete this user and try Sign Up again."
                    ),
                }
            return {
                "status": "success",
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": _user_payload(user),
            }
        except AuthError as e:
            message = str(e)
            lower = message.lower()
            if "already" in lower or "registered" in lower:
                return {"status": "error", "message": "That username is already taken"}
            return {"status": "error", "message": message}

    @staticmethod
    def sign_in(username: str, password: str) -> dict:
        try:
            username = _normalize_username(username)
            err = _validate_username(username)
            if err:
                return {"status": "error", "message": err}
            result = supabase.auth.sign_in_with_password({
                "email": _username_to_email(username),
                "password": password,
            })
            session = result.session
            user = result.user
            if not session or not user:
                return {"status": "error", "message": "Invalid username or password"}
            return {
                "status": "success",
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": _user_payload(user),
            }
        except AuthError as e:
            message = str(e)
            lower = message.lower()
            if "email not confirmed" in lower:
                return {
                    "status": "error",
                    "message": (
                        "This account still needs email confirmation in Supabase. "
                        "Disable Confirm email, delete the user under Authentication → Users, "
                        "then Sign Up again."
                    ),
                }
            if "invalid" in lower:
                return {"status": "error", "message": "Invalid username or password"}
            return {"status": "error", "message": message}

    @staticmethod
    def sign_out(access_token: str) -> dict:
        try:
            client = user_client(access_token)
            client.auth.sign_out()
            return {"status": "success"}
        except AuthError as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_user(access_token: str) -> dict | None:
        try:
            result = supabase.auth.get_user(access_token)
            user = result.user
            if not user:
                return None
            return _user_payload(user)
        except AuthError as e:
            print(f"Error getting user: {e}")
            return None
