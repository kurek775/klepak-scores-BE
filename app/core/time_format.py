"""Time-value helpers for TIME_* activities.

Scores for time-based activities are stored canonically as *total seconds*
(a numeric string) in ``Record.value_raw``. The frontend handles entry/display;
the backend only needs to format seconds for CSV export.

Accepted input (comma or dot decimals; whitespace tolerated):
    "83"        -> 83 s
    "83.4"      -> 83.4 s
    "1:23"      -> 1 min 23 s
    "1:23.4"    -> 1 min 23.4 s
    "1:23:45"   -> 1 min 23.45 s   (mm:ss:cc — third group is the fraction)

Race times here never span hours, so a 3-part ``a:b:c`` is read as
mm:ss:fraction, NOT h:mm:ss.
"""

from __future__ import annotations

import re

_IS_UINT = re.compile(r"^\d+$")
_IS_DECIMAL = re.compile(r"^\d*\.?\d+$")


def parse_time_to_seconds(value: str | None) -> float | None:
    """Parse a human time string into total seconds, or ``None`` if invalid."""
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None

    parts = text.split(":")
    if len(parts) > 3:
        return None

    minutes = 0
    if len(parts) == 1:
        seconds_str = parts[0].strip()
    elif len(parts) == 2:
        m = parts[0].strip()
        if not _IS_UINT.match(m):
            return None
        minutes = int(m)
        seconds_str = parts[1].strip()
    else:
        # mm:ss:cc — the third colon group is a decimal fraction of the second.
        m, s, frac = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not (_IS_UINT.match(m) and _IS_UINT.match(s) and _IS_UINT.match(frac)):
            return None
        minutes = int(m)
        seconds_str = f"{s}.{frac}"

    if not _IS_DECIMAL.match(seconds_str):
        return None
    seconds = float(seconds_str)
    if seconds < 0:
        return None
    if len(parts) >= 2 and seconds >= 60:  # seconds must be < 60 when minutes present
        return None

    return round(minutes * 60 + seconds, 2)


def format_seconds(total_seconds: float | str | None) -> str:
    """Format total seconds as ``m:ss`` or ``m:ss.cc`` (minutes may exceed 59)."""
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

    minutes = whole // 60
    seconds = whole % 60
    base = f"{minutes}:{seconds:02d}"

    return f"{base}.{centis:02d}" if centis > 0 else base
