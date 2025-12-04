import datetime

import pytest

from opentaxii.taxii2.utils import taxii2_datetimeformat


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
