"""Application configuration.

Secrets are loaded from environment variables so they are not committed to Git.
"""
import os

from telethon import TelegramClient
from telethon.sessions import StringSession
from .library import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def _required(name: str, cast=str):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    try:
        return cast(value.strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid value for environment variable {name}") from exc


admin_user_id = _required("ADMIN_USER_ID", int)
api_id = _required("API_ID", int)
api_hash = _required("API_HASH")
helper_username = os.getenv("HELPER_USERNAME", "Sa1selfbot").strip().lstrip("@")
bot_token = _required("BOT_TOKEN")

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

if spotify_client_id and spotify_client_secret:
    client_credentials_manager = SpotifyClientCredentials(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
else:
    client_credentials_manager = None
    sp = None

# Render is non-interactive, so prefer SESSION_STRING when provided.
# Never put a session string in source control.
session_string = os.getenv("SESSION_STRING", "").strip()
session_name = os.getenv("SESSION_NAME", "TRself-MT").strip() or "TRself-MT"
if session_string:
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
else:
    client = TelegramClient(session_name, api_id, api_hash)

# Display/contact information used by the panels.
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Saleh681").strip().lstrip("@")
SUPPORT_URL = f"https://t.me/{SUPPORT_USERNAME}"
