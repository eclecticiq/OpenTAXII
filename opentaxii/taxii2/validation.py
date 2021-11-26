import json

from opentaxii.taxii2.exceptions import ValidationError
from stix2 import parse
from stix2.exceptions import STIXError


def validate_envelope(json_data: str, allow_custom: bool = False) -> None:
    """
    Validate if ``json_data`` is a valid taxii2 envelope.

    :param str json_data: the data to check
    :param bool allow_custom: if true, allow non-standard stix types
    """
    if not json_data:
        raise ValidationError("No data")
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid json: {str(e)}") from e
    if "objects" not in data:
        raise ValidationError("No objects")
    for item in data["objects"]:
        try:
            parse(item, allow_custom)
        except STIXError as e:
            raise ValidationError(
                f"Invalid stix object: {json.dumps(item)}; {str(e)}"
            ) from e
