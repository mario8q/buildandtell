import hashlib
import hmac
import time

DEFAULT_TOLERANCE_SECONDS = 600


def verify_signature(
    raw_body,
    signature_header,
    secret,
    tolerance=DEFAULT_TOLERANCE_SECONDS,
):
    if not raw_body or not signature_header or not secret:
        return False

    parts = {}
    for part in signature_header.split(','):
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        parts[key.strip()] = value.strip()

    timestamp = parts.get('t')
    signatures = [
        value
        for key, value in parts.items()
        if key in ('v0', 'v1')
    ]
    if not timestamp or not signatures:
        return False

    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False

    if abs(time.time() - timestamp_int) > tolerance:
        return False

    signed = timestamp.encode('utf-8') + b'.' + raw_body
    expected = hmac.new(
        secret.encode('utf-8'),
        signed,
        hashlib.sha256,
    ).hexdigest()
    return any(
        hmac.compare_digest(expected, signature)
        for signature in signatures
    )
