"""Utility functions for taxii2."""
import base64
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentaxii.taxii2.entities import STIXObject

DATETIMEFORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def taxii2_datetimeformat(input_value: datetime.datetime) -> str:
    """
    Format datetime according to taxii2 spec.

    :param `datetime.datetime` input_value: The datetime object to format

    :return: The taxii2 string representation of `input_value`
    :rtype: string
    """
    return input_value.astimezone(datetime.timezone.utc).strftime(DATETIMEFORMAT)


def get_next_param(obj: "STIXObject") -> bytes:
    """
    Get value for `next` based on :class:`STIXObject` instance.

    :param :class:`STIXObject` obj: The object to base the `next` param on

    :return: The value to use as `next` param
    :rtype: str
    """
    return base64.b64encode(f"{obj.date_added.isoformat()}|{obj.id}".encode("utf-8"))


def parse_next_param(next_param: bytes):
    """
    Parse provided `next_param` into kwargs to be used to filter stix objects.
    """
    date_added_str, obj_id = base64.b64decode(next_param).decode().split("|")
    date_added = datetime.datetime.strptime(
        date_added_str.split('+')[0], "%Y-%m-%dT%H:%M:%S.%f"
    ).replace(tzinfo=datetime.timezone.utc)
    return {"id": obj_id, "date_added": date_added}
