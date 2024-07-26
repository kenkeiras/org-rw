"""Test the Timestamp object."""

import pytest
from datetime import date, datetime
from org_rw import Timestamp


def test_init_with_datetime() -> None:
    datetime_obj: datetime = datetime(2024, 7, 20, 15, 45)

    ts: Timestamp = Timestamp(active=True, datetime_=datetime_obj)

    assert ts.active is True
    assert ts._year == 2024
    assert ts._month == 7
    assert ts._day == 20
    assert ts.hour == 15
    assert ts.minute == 45
    assert ts.dow is None
    assert ts.repetition is None


def test_init_with_date() -> None:
    date_obj: date = date(2024, 7, 20)

    ts: Timestamp = Timestamp(active=True, datetime_=date_obj)

    assert ts.active is True
    assert ts._year == 2024
    assert ts._month == 7
    assert ts._day == 20
    assert ts.hour is None
    assert ts.minute is None
    assert ts.dow is None
    assert ts.repetition is None


def test_init_with_year_month_day() -> None:
    ts: Timestamp = Timestamp(
        active=True,
        year=2024,
        month=7,
        day=20,
        hour=15,
        minute=45,
        dow="Saturday",
        repetition=".+1d",
    )

    assert ts.active is True
    assert ts._year == 2024
    assert ts._month == 7
    assert ts._day == 20
    assert ts.hour == 15
    assert ts.minute == 45
    assert ts.dow == "Saturday"
    assert ts.repetition == ".+1d"


def test_init_without_required_arguments() -> None:
    with pytest.raises(ValueError):
        Timestamp(active=True)


def test_init_with_partial_date_info() -> None:
    with pytest.raises(ValueError):
        Timestamp(active=True, year=2024, month=7)


def test_init_with_datetime_overrides_date_info() -> None:
    datetime_obj: datetime = datetime(2024, 7, 20, 15, 45)

    ts: Timestamp = Timestamp(
        active=True, year=2020, month=1, day=1, datetime_=datetime_obj
    )

    assert ts.active is True
    assert ts._year == 2024
    assert ts._month == 7
    assert ts._day == 20
    assert ts.hour == 15
    assert ts.minute == 45
    assert ts.dow is None
    assert ts.repetition is None
