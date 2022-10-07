"""Taxii2 http helper functions."""
import json
from typing import Dict, Optional

from flask import Response, make_response
from uuid import UUID


class Taxii2JSONEncoder(json.JSONEncoder):
    """
    Extended JSONEncoder class with additional data types support.
    """
    def default(self, o):
        """Implements UUID serialization"""
        if isinstance(o, UUID):
            return str(o)

        return super().default(o)


def make_taxii2_response(data, status: Optional[int] = 200, extra_headers: Optional[Dict] = None) -> Response:
    """Turn input data into valid taxii2 response."""
    if not isinstance(data, str):
        data = json.dumps(data, cls=Taxii2JSONEncoder)
    response = make_response((data, status))
    response.content_type = "application/taxii+json;version=2.1"
    response.headers.update(extra_headers or {})
    return response
