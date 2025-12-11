import hashlib
import hmac
import json
from typing import Any, Dict, Optional


def compute_hash(data: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
    """Compute SHA-256 hash for tamper-evidence."""
    hash_input = {
        "timestamp": str(data.get("timestamp")),
        "event_type": data.get("event_type"),
        "severity": data.get("severity"),
        "source_service": data.get("source_service"),
        "user_id": data.get("user_id"),
        "action": data.get("action"),
        "resource": data.get("resource"),
        "result": data.get("result"),
        "detection_type": data.get("detection_type"),
        "metadata": data.get("metadata"),
        "previous_hash": previous_hash or "",
    }
    
    hash_string = json.dumps(hash_input, sort_keys=True, default=str)
    return hashlib.sha256(hash_string.encode()).hexdigest()


def sign_event(data: Dict[str, Any], secret: str) -> str:
    """Create HMAC signature for event."""
    message = json.dumps(data, sort_keys=True, default=str)
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    )
    return signature.hexdigest()


def verify_signature(data: Dict[str, Any], signature: str, secret: str) -> bool:
    """Verify HMAC signature."""
    expected = sign_event(data, secret)
    return hmac.compare_digest(expected, signature)


def verify_chain(current_hash: str, current_data: Dict[str, Any], previous_hash: Optional[str]) -> bool:
    """Verify hash chain integrity."""
    expected_hash = compute_hash(current_data, previous_hash)
    return hmac.compare_digest(expected_hash, current_hash)
