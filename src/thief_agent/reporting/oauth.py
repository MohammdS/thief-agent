"""Build a Gmail service with OAuth send-only credentials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def build_gmail_service(credentials_path: Path, token_path: Path) -> Any:
    """Load, refresh, or interactively create send-only Gmail credentials."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]
    from googleapiclient.discovery import build  # type: ignore[import-untyped]

    scopes = [GMAIL_SEND_SCOPE]
    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
            str(token_path), scopes,
        )
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
        credentials = flow.run_local_server(port=0)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)
