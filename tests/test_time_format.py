"""Unit tests for time-value parsing/formatting helpers."""

import pytest

from app.core.time_format import format_seconds, parse_time_to_seconds


@pytest.mark.parametrize(
    "value,expected",
    [
        ("83", 83.0),
        ("83.4", 83.4),
        ("1:23", 83.0),
        ("1:23.4", 83.4),
        ("0:05", 5.0),
        ("1:02:03", 3723.0),
        ("1:02:03.5", 3723.5),
        ("1:23,4", 83.4),  # comma decimal
        (" 1:23 ", 83.0),  # surrounding whitespace
    ],
)
def test_parse_valid(value, expected):
    assert parse_time_to_seconds(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
        "abc",
        "1:2:3:4",   # too many segments
        "45:74",     # seconds >= 60 with minutes present
        "1:60:00",   # minutes >= 60 in h:mm:ss
        "1.5:20",    # fractional minutes
        "-5",        # negative
    ],
)
def test_parse_invalid(value):
    assert parse_time_to_seconds(value) is None


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (83, "1:23"),
        (83.4, "1:23.40"),
        (5, "0:05"),
        (3723, "1:02:03"),
        (3723.5, "1:02:03.50"),
        (0, "0:00"),
    ],
)
def test_format(seconds, expected):
    assert format_seconds(seconds) == expected


def test_format_invalid_returns_empty():
    assert format_seconds(None) == ""
    assert format_seconds("nope") == ""
    assert format_seconds(-1) == ""


def test_round_trip():
    for original in ["1:23.40", "0:05", "1:02:03.50", "12:00"]:
        secs = parse_time_to_seconds(original)
        assert secs is not None
        assert format_seconds(secs) == original
