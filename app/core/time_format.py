"""Time-value helpers for TIME_* activities.

Scores for time-based activities are stored canonically as *total seconds*
(a numeric string) in ``Record.value_raw``. The frontend handles entry/display
in ``m:ss.cc`` form; the backend only needs to format seconds for CSV export.
"""

from __future__ import annotations


def parse_time_to_seconds(value: str | None) -> float | None:
    """Parse a human time string into total seconds.

    Accepts ``"83"``, ``"83.4"``, ``"1:23"``, ``"1:23.4"``, ``"1:02:03.5"``
    (comma or dot decimals). Returns ``None`` for empty or malformed input.
    Rejects out-of-range segments (seconds/minutes >= 60 when a larger unit is
    present) so a mistyped ``"45:74"`` does not silently become a valid time.
    """
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    parts = text.split(":")
    if len(parts) > 3:
        return None

    total = 0.0
    n = len(parts)
    for i, raw in enumerate(parts):
        part = raw.strip()
        try:
            num = float(part)
        except ValueError:
            return None
        if num < 0:
            return None
        is_last = i == n - 1
        # Only the final (seconds) segment may be fractional.
        if not is_last and num != int(num):
            return None
        # When a larger unit precedes it, seconds must be < 60.
        if n >= 2 and is_last and num >= 60:
            return None
        # In h:mm:ss form, minutes must be < 60.
        if n == 3 and i == 1 and num >= 60:
            return None
        total = total * 60 + num

    return round(total, 2)


def format_seconds(total_seconds: float | str | None) -> str:
    """Format total seconds as ``m:ss`` or ``m:ss.cc`` (with hours if >= 1h)."""
    if total_seconds is None:
        return ""
    try:
        ts = float(total_seconds)
    except (ValueError, TypeError):
        return ""
    if ts < 0:
        return ""

    ts = round(ts, 2)
    whole = int(ts)
    centis = round((ts - whole) * 100)
    if centis == 100:  # rounding carried over
        whole += 1
        centis = 0

    hours = whole // 3600
    minutes = (whole % 3600) // 60
    seconds = whole % 60

    if hours > 0:
        base = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        base = f"{minutes}:{seconds:02d}"

    return f"{base}.{centis:02d}" if centis > 0 else base
