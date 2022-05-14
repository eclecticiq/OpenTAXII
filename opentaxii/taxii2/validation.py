"""Taxii2 validation functions."""
import datetime
import json

from marshmallow import Schema, fields
from opentaxii.persistence.api import OpenTAXII2PersistenceAPI
from opentaxii.taxii2.exceptions import ValidationError
from opentaxii.taxii2.utils import DATETIMEFORMAT
from stix2 import parse
from stix2.exceptions import STIXError
from werkzeug.datastructures import ImmutableMultiDict


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


class Taxii2DateTime(fields.DateTime):
    """Taxii2 formatting compliant datetime field."""

    DEFAULT_FORMAT = DATETIMEFORMAT

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.replace(tzinfo=datetime.timezone.utc)


class Taxii2Next(fields.Field):
    """Implemenatation of the taxii2 `next` query param."""

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        try:
            value = self.parent.persistence_api.parse_next_param(value)
        except:  # noqa
            raise ValidationError("Not a valid value.")
        return value


class Taxii2Filter(fields.Field):
    """General taxii2 filter implementation."""

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.split(",")


class Taxii2VersionFilter(Taxii2Filter):
    """Taxii2 compliant version filter."""

    def _deserialize(self, value, attr, data, **kwargs):
        values = super()._deserialize(value, attr, data, **kwargs)
        new_values = []
        for value in values:
            if value not in ["first", "last", "all"]:
                try:
                    value = datetime.datetime.strptime(value, DATETIMEFORMAT).replace(
                        tzinfo=datetime.timezone.utc
                    )
                except ValueError:
                    pass
            new_values.append(value)
        return new_values


class PersistenceApiMxin:
    """Store persistence api on schema instance, to reference in `Taxii2Next`"""
    def __init__(self, persistence_api: OpenTAXII2PersistenceAPI, *args, **kwargs):
        self.persistence_api = persistence_api
        super().__init__(*args, **kwargs)


class VersionFilterParamsSchema(PersistenceApiMxin, Schema):
    """Schema for the versions endpoint filters."""

    limit = fields.Int()
    added_after = Taxii2DateTime()
    next_kwargs = Taxii2Next(data_key="next")
    match_spec_version = Taxii2Filter(data_key="match[spec_version]")


class ObjectFilterParamsSchema(PersistenceApiMxin, Schema):
    """Schema for the object endpoint filters."""

    limit = fields.Int()
    added_after = Taxii2DateTime()
    next_kwargs = Taxii2Next(data_key="next")
    match_spec_version = Taxii2Filter(data_key="match[spec_version]")
    match_version = Taxii2VersionFilter(data_key="match[version]")


class ListFilterParamsSchema(PersistenceApiMxin, Schema):
    """Schema for the object list endpoint filters."""

    limit = fields.Int()
    added_after = Taxii2DateTime()
    next_kwargs = Taxii2Next(data_key="next")
    match_spec_version = Taxii2Filter(data_key="match[spec_version]")
    match_version = Taxii2VersionFilter(data_key="match[version]")
    match_id = Taxii2Filter(data_key="match[id]")
    match_type = Taxii2Filter(data_key="match[type]")


class DeleteFilterParamsSchema(Schema):
    """Schema for the object delete endpoint filters."""

    match_version = Taxii2VersionFilter(data_key="match[version]")
    match_spec_version = Taxii2Filter(data_key="match[spec_version]")


def validate_object_filter_params(
    filter_params: ImmutableMultiDict, persistence_api: OpenTAXII2PersistenceAPI
) -> dict:
    """Validate and load filter params for the object endpoint."""
    parsed_params = ObjectFilterParamsSchema(persistence_api).load(filter_params)
    return parsed_params


def validate_list_filter_params(
    filter_params: ImmutableMultiDict, persistence_api: OpenTAXII2PersistenceAPI
) -> dict:
    """Validate and load filter params for the list endpoint."""
    parsed_params = ListFilterParamsSchema(persistence_api).load(filter_params)
    return parsed_params


def validate_versions_filter_params(
    filter_params: ImmutableMultiDict, persistence_api: OpenTAXII2PersistenceAPI
) -> dict:
    """Validate and load filter params for the versions endpoint."""
    parsed_params = VersionFilterParamsSchema(persistence_api).load(filter_params)
    return parsed_params


def validate_delete_filter_params(filter_params: ImmutableMultiDict) -> dict:
    """Validate and load filter params for the delete endpoint."""
    parsed_params = DeleteFilterParamsSchema().load(filter_params)
    return parsed_params
