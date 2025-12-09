import json
import platform

import pytest

from opentaxii.taxii2.exceptions import ValidationError
from opentaxii.taxii2.validation import validate_envelope
from tests.utils import conditional

BROKEN_INDICATOR = json.dumps(
    {
        "objects": [
            {
                "type": "indicator",
                "id": "indicator--c410e480-e42b-47d1-9476-85307c12bcbf",
            }
        ]
    }
)
GOOD_INDICATOR_WITH_CONTEXT = json.dumps(
    {
        "objects": [
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                "created": "2016-04-06T20:03:48.000Z",
                "modified": "2016-04-06T20:03:48.000Z",
                "indicator_types": ["malicious-activity"],
                "name": "Poison Ivy Malware",
                "description": "This file is part of Poison Ivy",
                "pattern": "[ file:hashes.'SHA-256' = "
                "'4bac27393bdd9777ce02453256c5577cd02275510b2227f473d03f533924f877' ]",
                "pattern_type": "stix",
                "valid_from": "2016-01-01T00:00:00Z",
            },
            {
                "type": "relationship",
                "spec_version": "2.1",
                "id": "relationship--44298a74-ba52-4f0c-87a3-1824e67d7fad",
                "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                "created": "2016-04-06T20:06:37.000Z",
                "modified": "2016-04-06T20:06:37.000Z",
                "relationship_type": "indicates",
                "source_ref": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
                "target_ref": "malware--31b940d4-6f7f-459a-80ea-9c1f17b5891b",
            },
            {
                "type": "malware",
                "spec_version": "2.1",
                "id": "malware--31b940d4-6f7f-459a-80ea-9c1f17b5891b",
                "is_family": True,
                "created": "2016-04-06T20:07:09.000Z",
                "modified": "2016-04-06T20:07:09.000Z",
                "created_by_ref": "identity--f431f809-377b-45e0-aa1c-6a4751cae5ff",
                "name": "Poison Ivy",
                "malware_types": ["trojan"],
            },
        ]
    }
)
CUSTOM_TYPE = json.dumps({"objects": [{"type": "mytype"}]})

if platform.python_implementation() == "PyPy":
    JSON_ERROR_MESSAGE = "Invalid json: Unexpected 'a': line 1 column 1 (char 0)"
else:
    JSON_ERROR_MESSAGE = "Invalid json: Expecting value: line 1 column 1 (char 0)"


@pytest.mark.parametrize(
    ["json_data", "allow_custom", "raises", "message"],
    [
        (None, False, True, "No data"),
        ("", False, True, "No data"),
        ("{}", False, True, "No objects"),
        ("abcd", False, True, JSON_ERROR_MESSAGE),
        (
            BROKEN_INDICATOR,
            False,
            True,
            'Invalid stix object: {"type": "indicator", "id": "indicator--c410e480-e42b-47d1-9476-85307c12bcbf"};'
            " No values for required properties for Indicator: (labels, pattern).",
        ),
        (GOOD_INDICATOR_WITH_CONTEXT, False, False, ""),
        (
            CUSTOM_TYPE,
            False,
            True,
            'Invalid stix object: {"type": "mytype"}; Can\'t parse unknown object type'
            " 'mytype'! For custom types, use the CustomObject decorator.",
        ),
        (
            CUSTOM_TYPE,
            True,
            False,
            "",
        ),
    ],
)
def test_validate_envelope(json_data, allow_custom, raises, message):
    with conditional(raises, pytest.raises(ValidationError)) as exception:
        validate_envelope(json_data, allow_custom)
    if raises:
        assert str(exception.value) == message
