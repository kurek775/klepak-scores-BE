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
        # mm:ss:cc — third colon group is the fractional part
        ("1:23:45", 83.45),
        ("1:23:5", 83.5),
        ("0:59:99", 59.99),
        ("1:02:03", 62.03),
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
        "1:60:00",   # seconds segment >= 60 in mm:ss:cc
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
        (83.45, "1:23.45"),
        (5, "0:05"),
        (0, "0:00"),
        (3723, "62:03"),      # no hour rollover — minutes may exceed 59
        (3723.5, "62:03.50"),
    ],
)
def test_format(seconds, expected):
    assert format_seconds(seconds) == expected


def test_format_invalid_returns_empty():
    assert format_seconds(None) == ""
    assert format_seconds("nope") == ""
    assert format_seconds(-1) == ""


def test_round_trip():
    for original in ["1:23.45", "0:05", "62:03.50", "12:00"]:
        secs = parse_time_to_seconds(original)
        assert secs is not None
        assert format_seconds(secs) == original


def test_colon_fraction_formats_back_with_dot():
    assert format_seconds(parse_time_to_seconds("1:23:45")) == "1:23.45"
