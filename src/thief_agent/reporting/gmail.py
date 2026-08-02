"""Dry-run-first Gmail JSON attachment delivery."""

from __future__ import annotations

import asyncio
import base64
import hashlib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Literal

from thief_agent.artifacts.result import ResultArtifact, result_sha256
from thief_agent.reliability.checkpoint import CheckpointStore
from thief_agent.reporting.duplicates import DuplicateRegistry
from thief_agent.reporting.gatekeeper import ReportingGatekeeper
from thief_agent.reporting.oauth import build_gmail_service

RECIPIENT = "rmisegal+uoh26finalgame@gmail.com"


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    """Describe a dry-run or successful Gmail delivery."""

    mode: Literal["dry-run", "live"]
    attachment_sha256: str
    message_id: str | None
    dry_run_path: Path | None


class GmailReporter:
    """Deliver one agreed JSON result with duplicate and abuse protection."""

    def __init__(
        self,
        mode: Literal["dry-run", "live"],
        state_dir: Path,
        gatekeeper: ReportingGatekeeper,
        credentials_path: Path = Path("credentials.json"),
        token_path: Path = Path("token.json"),
        service: Any = None,
    ) -> None:
        """Configure safe delivery without loading OAuth during dry-run."""
        self._mode, self._state_dir, self._gatekeeper = mode, state_dir, gatekeeper
        self._credentials_path, self._token_path = credentials_path, token_path
        self._service = service
        self._duplicates = DuplicateRegistry(state_dir / "delivered.json")

    async def send(self, result_path: Path) -> DeliveryReceipt:
        """Dry-run or send one unique JSON attachment."""
        attachment = result_path.read_bytes()
        result = ResultArtifact.model_validate_json(attachment)
        if not result.mutual_agreement.confirmed:
            raise ValueError("result must have mutual agreement before reporting")
        if result.mutual_agreement.sha256 != result_sha256(result):
            raise ValueError("result agreement hash is invalid")
        digest = hashlib.sha256(attachment).hexdigest()
        self._duplicates.ensure_new(digest)
        raw = build_raw_message(result_path.name, attachment)
        if self._mode == "dry-run":
            path = self._state_dir / f"dry-run-{digest[:12]}.json"
            CheckpointStore(path).save({"raw": raw, "attachment_sha256": digest})
            self._duplicates.record(digest)
            return DeliveryReceipt("dry-run", digest, None, path)
        response = await self._gatekeeper.call(lambda: self._send_live(raw))
        message_id = str(response.get("id", "")) or None
        self._duplicates.record(digest)
        return DeliveryReceipt("live", digest, message_id, None)

    async def _send_live(self, raw: str) -> dict[str, Any]:
        """Execute one synchronous Gmail API call in a bounded worker thread."""
        service = self._service or build_gmail_service(
            self._credentials_path, self._token_path,
        )

        def execute() -> dict[str, Any]:
            try:
                response = service.users().messages().send(
                    userId="me", body={"raw": raw},
                ).execute()
            except Exception as error:
                raise OSError("Gmail API request failed") from error
            if not isinstance(response, dict):
                raise OSError("Gmail API returned a non-object response")
            return response

        return await asyncio.to_thread(execute)


def build_raw_message(filename: str, attachment: bytes) -> str:
    """Build a send-only MIME message with one JSON attachment."""
    message = EmailMessage()
    message["To"] = RECIPIENT
    message["Subject"] = f"Police-and-Thief result: {filename}"
    message.set_content("Attached is the independently agreed machine-readable result.")
    message.add_attachment(
        attachment,
        maintype="application",
        subtype="json",
        filename=filename,
    )
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
