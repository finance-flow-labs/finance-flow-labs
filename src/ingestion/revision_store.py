import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class PutResult:
    status: str
    revision_number: int


class RevisionStore:
    def __init__(self) -> None:
        self._rows: dict[str, list[str]] = {}

    def put(self, idempotency_key: str, payload: Mapping[str, object]) -> PutResult:
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        hashes = self._rows.setdefault(idempotency_key, [])
        if not hashes:
            hashes.append(payload_hash)
            return PutResult(status="inserted", revision_number=1)
        if hashes[-1] == payload_hash:
            return PutResult(status="noop", revision_number=len(hashes))
        hashes.append(payload_hash)
        return PutResult(status="revision", revision_number=len(hashes))
