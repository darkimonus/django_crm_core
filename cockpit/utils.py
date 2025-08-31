import json
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional
from datetime import datetime, timezone

from dateutil import parser as dateparser


def ensure_aware(ts: datetime) -> datetime:
    """
    Returns timezone-aware datetime (UTC).
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def parse_change_ts(value: Any) -> datetime:
    """
    Accepts datetime or string (ISO/RFC3339) and returns aware UTC datetime.
    """
    if isinstance(value, datetime):
        return ensure_aware(value)
    return ensure_aware(dateparser.isoparse(str(value)))


def normalize_value(kind: str, value: Any) -> str:
    """
    Business value normalization for stable hashdiff.
    TEXT -> lower().strip()
    NUM  -> Decimal with constant precision
    TS   -> ISO in UTC without microseconds
    BOOL -> "true"/"false"
    JSON -> canonical JSON (sort_keys, no spaces)
    """
    k = (kind or "").upper()
    match k:
        case "TEXT":
            return (value or "").strip().lower()
        case "NUM":
            if value is None:
                return ""
            d = Decimal(str(value)).quantize(Decimal("0.000000"), rounding=ROUND_HALF_UP)
            return format(d, "f")
        case "TS":
            if value is None:
                return ""
            ts = value if isinstance(value, datetime) else dateparser.isoparse(str(value))
            ts = ensure_aware(ts).replace(microsecond=0)
            return ts.isoformat().replace("+00:00", "Z")
        case "BOOL":
            return "true" if bool(value) else "false"
        case "JSON":
            return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        case _:
            return "" if value is None else str(value)


def calc_hashdiff(*parts: Optional[str]) -> str:
    """
    Calculate sha256 from concatenation of normalized parts with '|' as separator.
    Suitable for both Entity and EntityDetail.
    """
    joined = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
