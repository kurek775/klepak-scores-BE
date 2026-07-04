"""Small text helpers: diacritic stripping and slugification."""

import re
import unicodedata


def deaccent(value: str) -> str:
    """Remove diacritics, e.g. 'Letní tábor' -> 'Letni tabor'."""
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slugify(value: str) -> str:
    """ASCII, lowercase, hyphen-separated slug. 'Piškoti 2026' -> 'piskoti-2026'."""
    ascii_str = deaccent(value).lower()
    ascii_str = re.sub(r"[^a-z0-9]+", "-", ascii_str)
    return ascii_str.strip("-") or "x"
