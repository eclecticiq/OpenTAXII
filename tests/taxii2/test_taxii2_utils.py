import datetime

import pytest
from opentaxii.taxii2.utils import (get_next_param, parse_next_param,
                                    taxii2_datetimeformat)
from tests.taxii2.factories import STIXObjectFactory


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


@pytest.mark.parametrize(
    "stix_id, date_added, next_param",
    [
        pytest.param(
            "indicator--fa641b92-94d7-42dd-aa0e-63cfe1ee148a",
            datetime.datetime(
                2022, 2, 4, 18, 40, 6, 297204, tzinfo=datetime.timezone.utc
            ),
            (
                b"MjAyMi0wMi0wNFQxODo0MDowNi4yOTcyMDQrMDA6MDB8aW5kaWNhdG9yLS1mYTY0M"
                b"WI5Mi05NGQ3LTQyZGQtYWEwZS02M2NmZTFlZTE0OGE="
            ),
            id="simple",
        ),
    ],
)
def test_next_param(stix_id, date_added, next_param):
    stix_object = STIXObjectFactory.build(
        id=stix_id,
        type=stix_id.split("--")[0],
        date_added=date_added,
    )
    assert get_next_param(stix_object) == next_param
    assert parse_next_param(next_param) == {"id": stix_id, "date_added": date_added}
