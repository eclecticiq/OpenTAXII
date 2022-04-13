"""Factories for taxii2 entities."""
import datetime
from uuid import uuid4

import factory
import stix2
from opentaxii.taxii2.entities import STIXObject


class STIXObjectFactory(factory.Factory):
    id = factory.LazyAttribute(lambda o: f"{o.type}--{str(uuid4())}")
    collection_id = factory.Faker("uuid4")
    type = factory.Faker("random_element", elements=tuple(stix2.v21.OBJ_MAP.keys()))
    spec_version = factory.Faker("random_element", elements=("2.0", "2.1"))
    date_added = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    version = factory.Faker("date_time", tzinfo=datetime.timezone.utc)
    serialized_data = factory.Faker(
        "pydict"
    )  # TODO replace with valid stix object data generator

    class Meta:
        model = STIXObject
