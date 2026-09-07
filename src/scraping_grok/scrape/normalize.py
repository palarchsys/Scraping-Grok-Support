"""Normalisation titre / texte / date — le contrat SQL est du texte propre UTC."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from dateutil import parser as date_parser
from dateutil import tz

_WS = re.compile(r"\s+")
_BOILER = re.compile(
    r"(Lire aussi|À voir également|Newsletter|Partager cet article).*$",
    re.I | re.S,
)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = _BOILER.sub("", value)
    return _WS.sub(" ", text).strip()


def parse_date(value: str | None, timezone_name: str) -> datetime | None:
    """RSS date, ISO, ou relatif. Naive → timezone source. Sortie UTC."""
    if not value:
        return None
    value = value.strip()
    dt: datetime | None = None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        dt = None
    if dt is None:
        try:
            dt = date_parser.parse(value, fuzzy=True)
        except (ValueError, OverflowError, TypeError):
            return None
    if dt.tzinfo is None:
        zone = tz.gettz(timezone_name) or timezone.utc
        dt = dt.replace(tzinfo=zone)
    return dt.astimezone(timezone.utc)
