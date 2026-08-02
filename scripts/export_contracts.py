"""Export stable JSON Schemas from the authoritative Pydantic wire models."""

from __future__ import annotations

import json
from pathlib import Path

from thief_agent.crypto.audit import FinalAuditRequest
from thief_agent.protocol.messages import (
    CaptureClaimRequest,
    CommitTurnRequest,
    HealthRequest,
    NegotiationRequest,
    ResultProposalRequest,
    RevealTurnRequest,
)

MODELS = {
    "health": HealthRequest,
    "negotiate": NegotiationRequest,
    "commit_turn": CommitTurnRequest,
    "reveal_turn": RevealTurnRequest,
    "capture_claim": CaptureClaimRequest,
    "final_audit": FinalAuditRequest,
    "propose_result": ResultProposalRequest,
}


def main() -> int:
    """Write one deterministic schema file per public tool."""
    output = Path("contracts/schemas")
    output.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        (output / f"{name}.schema.json").write_text(schema, encoding="utf-8")
    print(f"Exported {len(MODELS)} protocol schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

