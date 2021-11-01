import datetime

import pytest

from fixtures import COLLECTION_OPEN, COLLECTIONS_A


@pytest.mark.parametrize("with_messages", [True, False])
def test_delete_content_blocks(app, with_messages):
    app.taxii_server.persistence.create_collection(COLLECTIONS_A[0])
    app.taxii_server.persistence.delete_content_blocks(
        COLLECTION_OPEN,
        start_time=datetime.datetime.now(datetime.timezone.utc),
        with_messages=with_messages,
    )
