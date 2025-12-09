import pytest

from opentaxii.auth.sqldb.models import Account


def test_account_permissions(app):
    account = Account()

    account.permissions = {
        "taxii1-read": "read",
        "taxii1-modify": "modify",
        "taxii2-both": ["read", "write"],
        "taxii2-read": ["read"],
        "taxii2-write": ["write"],
    }
    assert account.permissions == {
        "taxii1-read": "read",
        "taxii1-modify": "modify",
        "taxii2-both": ["read", "write"],
        "taxii2-read": ["read"],
        "taxii2-write": ["write"],
    }

    with pytest.raises(
        ValueError,
        match=r"Unknown TAXII1 permission 'bad' specified for collection 'taxii1-fail'",
    ):
        account.permissions = {"taxii1-fail": "bad"}

    with pytest.raises(
        ValueError,
        match=r"Unknown TAXII2 permission '\['read', 'bad'\]' specified for collection 'taxii2-fail'",
    ):
        account.permissions = {"taxii2-fail": ["read", "bad"]}
