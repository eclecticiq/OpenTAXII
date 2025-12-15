import datetime

import pytest

from opentaxii.taxii2.utils import get_object_version, taxii2_datetimeformat


@pytest.mark.parametrize(
    ["input_value", "expected"],
    [
        pytest.param(
            datetime.datetime(2022, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc),
            "2022-01-01T12:00:00.000000Z",
            id="utc",
        ),
        pytest.param(
            datetime.datetime(
                2022,
                1,
                1,
                12,
                0,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
            ),
            "2022-01-01T11:00:00.000000Z",
            id="utc+1",
        ),
        pytest.param(
            datetime.datetime(
                2022,
                1,
                1,
                12,
                0,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1, minutes=30)),
            ),
            "2022-01-01T10:30:00.000000Z",
            id="utc+1.5",
        ),
        pytest.param(
            datetime.datetime(
                2022,
                1,
                1,
                12,
                0,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=-1)),
            ),
            "2022-01-01T13:00:00.000000Z",
            id="utc+1",
        ),
        pytest.param(
            datetime.datetime(
                2022,
                1,
                1,
                12,
                0,
                0,
                0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=-1, minutes=-30)),
            ),
            "2022-01-01T13:30:00.000000Z",
            id="utc+1.5",
        ),
    ],
)
def test_taxii2_datetimeformat(input_value, expected):
    assert taxii2_datetimeformat(input_value) == expected


def test_get_object_version():
    assert get_object_version(
        {
            "modified": "2022-01-01T13:30:00.000000Z",
            "created": "2016-04-06T20:06:37.000Z",
        }
    ) == datetime.datetime(2022, 1, 1, 13, 30, 00, 0, datetime.timezone.utc)
    assert get_object_version(
        {"created": "2016-04-06T20:06:37.000Z"}
    ) == datetime.datetime(2016, 4, 6, 20, 6, 37, 0, datetime.timezone.utc)
    assert get_object_version({}) == datetime.datetime.fromtimestamp(
        0, tz=datetime.timezone.utc
    )
