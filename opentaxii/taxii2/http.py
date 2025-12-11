"""Taxii2 http helper functions."""

import json
import uuid
from typing import Dict, Optional

from flask import Response, make_response


class UuidJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def make_taxii2_response(
    data, status: Optional[int] = 200, extra_headers: Optional[Dict] = None
) -> Response:
    """Turn input data into valid taxii2 response."""
    if not isinstance(data, str):
        data = json.dumps(data, cls=UuidJsonEncoder)
    response = make_response((data, status))
    response.content_type = "application/taxii+json;version=2.1"
    response.headers.update(extra_headers or {})
    return response
