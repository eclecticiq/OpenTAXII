"""Utility functions for taxii2."""

import datetime

DATETIMEFORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def taxii2_datetimeformat(input_value: datetime.datetime) -> str:
    """
    Format datetime according to taxii2 spec.

    :param `datetime.datetime` input_value: The datetime object to format

    :return: The taxii2 string representation of `input_value`
    :rtype: string
    """
    return input_value.astimezone(datetime.timezone.utc).strftime(DATETIMEFORMAT)


def get_object_version(obj: dict) -> datetime.datetime:
    if "modified" in obj:
        return datetime.datetime.strptime(obj["modified"], DATETIMEFORMAT).replace(
            tzinfo=datetime.timezone.utc
        )
    elif "created" in obj:
        return datetime.datetime.strptime(obj["created"], DATETIMEFORMAT).replace(
            tzinfo=datetime.timezone.utc
        )
    else:
        # If a STIX object is not versioned (and therefore does not have a modified
        # timestamp) then this version parameter MUST use the created timestamp. If
        # an object does not have a created or modified timestamp or any other
        # version information that can be used, then the server should use a value for
        # the version that is consistent to the server.
        # -- TAXII 2.1 specification --
        return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
