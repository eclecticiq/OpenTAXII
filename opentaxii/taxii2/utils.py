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
