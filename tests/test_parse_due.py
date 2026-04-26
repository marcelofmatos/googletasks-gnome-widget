"""parse_due: conversão de strings RFC 3339 para date."""
from datetime import date

from main import parse_due


def test_rfc3339_utc_z_suffix():
    assert parse_due("2025-06-15T00:00:00.000Z") == date(2025, 6, 15)


def test_rfc3339_with_offset():
    assert parse_due("2025-06-15T00:00:00+00:00") == date(2025, 6, 15)


def test_rfc3339_with_timezone():
    assert parse_due("2025-06-15T12:00:00-03:00") == date(2025, 6, 15)


def test_empty_string_returns_none():
    assert parse_due("") is None


def test_none_returns_none():
    assert parse_due(None) is None


def test_invalid_format_returns_none():
    assert parse_due("not-a-date") is None
