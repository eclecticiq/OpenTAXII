import os
from unittest import mock

import pytest

from opentaxii.cli.auth import create_account, update_account
from opentaxii.cli.persistence import (
    add_api_root,
    add_collection,
    delete_content_blocks,
    job_cleanup,
    sync_data_configuration,
)
from tests.fixtures import ACCOUNT, COLLECTION_OPEN
from tests.taxii2.utils import API_ROOTS
from tests.utils import assert_str_equal_no_formatting, conditional_raises


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr"],
    [
        pytest.param(
            [os.path.join("examples", "data-configuration.yml")],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            id="default",
        ),
        pytest.param(
            [os.path.join("examples", "data-configuration.yml"), "-f"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            id="default, -f",
        ),
        pytest.param(
            [
                os.path.join("examples", "data-configuration.yml"),
                "--force-delete",
            ],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            id="default, --force-delete",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "[-f]",
                    "config",
                    ":error: the following arguments are required: config",
                ]
            ),
            id="no args",
        ),
        pytest.param(
            ["this_file_does_not_exist"],  # argv
            FileNotFoundError,  # raises
            "[Errno 2] No such file or directory: 'this_file_does_not_exist'",  # message
            "",  # stdout
            "",  # stderr
            id="missing config",
        ),
        pytest.param(
            ["this_file_does_not_exist", "-f"],  # argv
            FileNotFoundError,  # raises
            "[Errno 2] No such file or directory: 'this_file_does_not_exist'",  # message
            "",  # stdout
            "",  # stderr
            id="missing config, with -f",
        ),
    ],
)
def test_sync_data_configuration(app, capsys, argv, raises, message, stdout, stderr):
    with (
        mock.patch("opentaxii.cli.persistence.app", app),
        mock.patch("sys.argv", [""] + argv),
    ):
        with conditional_raises(raises) as exception:
            sync_data_configuration()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr"],
    [
        pytest.param(
            ["-c", COLLECTION_OPEN, "--begin", "2000-01-01"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            id="good",
        ),
        pytest.param(
            ["-c", "collectiondoesnotexist", "--begin", "2000-01-01"],  # argv
            ValueError,  # raises
            "Collection with name 'collectiondoesnotexist' does not exist",  # message
            "",  # stdout
            "",  # stderr
            id="collection does not exist",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-c COLLECTION",
                    "[-m]",
                    "--begin BEGIN",
                    "[--end END]",
                    ": error: the following arguments are required: -c/--collection, --begin",
                ]
            ),
            id="no args",
        ),
    ],
)
def test_delete_content_blocks(
    app, collections, capsys, argv, raises, message, stdout, stderr
):
    with (
        mock.patch("opentaxii.cli.persistence.app", app),
        mock.patch("sys.argv", [""] + argv),
    ):
        with conditional_raises(raises) as exception:
            delete_content_blocks()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr", "expected_call"],
    [
        pytest.param(
            ["-u", "myuser", "-p", "mypass"],  # argv
            False,  # raises
            None,  # message
            "token: JWT_TOKEN",  # stdout
            "",  # stderr
            {  # expected_call
                "username": "myuser",
                "password": "mypass",
                "is_admin": False,
            },
            id="regular-user",
        ),
        pytest.param(
            ["-u", "myuser", "-p", "mypass", "-a"],  # argv
            False,  # raises
            None,  # message
            "token: JWT_TOKEN",  # stdout
            "",  # stderr
            {  # expected_call
                "username": "myuser",
                "password": "mypass",
                "is_admin": True,
            },
            id="admin",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-u USERNAME",
                    "-p PASSWORD",
                    "[-a]",
                    ": error: the following arguments are required: -u/--username, -p/--password",
                ]
            ),
            None,  # expected_call
            id="no args",
        ),
    ],
)
def test_create_account(
    app, capsys, argv, raises, message, stdout, stderr, expected_call
):
    with (
        mock.patch("opentaxii.cli.auth.app", app),
        mock.patch("sys.argv", [""] + argv),
        mock.patch.object(
            app.taxii_server.auth.api,
            "create_account",
            wraps=app.taxii_server.auth.api.create_account,
        ) as mock_create_account,
    ):
        with conditional_raises(raises) as exception:
            create_account()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)
        if expected_call is None:
            mock_create_account.assert_not_called()
        else:
            mock_create_account.assert_called_once_with(**expected_call)


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr"],
    [
        pytest.param(
            ["-u", ACCOUNT.username, "-f", "admin", "-v", "y"],  # argv
            False,  # raises
            None,  # message
            "now user is admin",  # stdout
            "",  # stderr
            id="make admin",
        ),
        pytest.param(
            ["-u", ACCOUNT.username, "-f", "admin", "-v", "n"],  # argv
            False,  # raises
            None,  # message
            "now user is mortal",  # stdout
            "",  # stderr
            id="drop admin",
        ),
        pytest.param(
            ["-u", ACCOUNT.username, "-f", "password", "-v", "newpass"],  # argv
            False,  # raises
            None,  # message
            "password has been changed",  # stdout
            "",  # stderr
            id="change password",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-u USERNAME",
                    "-f {password,admin}",
                    "-v VALUE",
                    ": error: the following arguments are required: -u/--username, -f/--field, -v/--value",
                ]
            ),
            id="no args",
        ),
    ],
)
def test_update_account(app, account, capsys, argv, raises, message, stdout, stderr):
    with mock.patch("opentaxii.cli.auth.app", app), mock.patch("sys.argv", [""] + argv):
        with conditional_raises(raises) as exception:
            update_account()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr", "expected_call"],
    [
        pytest.param(
            ["-t", "my new api root"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": None,
                "default": False,
                "is_public": False,
                "api_root_id": None,
            },  # expected_call
            id="title only",
        ),
        pytest.param(
            ["-t", "my new api root", "-d", "my description"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": "my description",
                "default": False,
                "is_public": False,
                "api_root_id": None,
            },  # expected_call
            id="title, description",
        ),
        pytest.param(
            ["-t", "my new api root", "--default"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": None,
                "default": True,
                "is_public": False,
                "api_root_id": None,
            },  # expected_call
            id="title, default",
        ),
        pytest.param(
            ["-t", "my new api root", "-d", "my description", "--default"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": "my description",
                "default": True,
                "is_public": False,
                "api_root_id": None,
            },  # expected_call
            id="title, description, default",
        ),
        pytest.param(
            ["-t", "my new api root", "--public"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": None,
                "default": False,
                "is_public": True,
                "api_root_id": None,
            },  # expected_call
            id="title, public",
        ),
        pytest.param(
            [
                "-t",
                "my new api root",
                "--id",
                "7468eafb-585d-402e-b6b9-49fe76492f9e",
            ],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "title": "my new api root",
                "description": None,
                "default": False,
                "is_public": False,
                "api_root_id": "7468eafb-585d-402e-b6b9-49fe76492f9e",
            },  # expected_call
            id="title, id",
        ),
        pytest.param(
            ["-t", "my new api root", "--id", "7468eafb-585d-402e-b6b9"],  # argv
            ValueError,  # raises
            "badly formed hexadecimal UUID string",  # message
            "",  # stdout
            "",  # stderr
            None,  # expected_call
            id="title, id (bad)",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-t TITLE",
                    "[-d DESCRIPTION]",
                    "[--default]",
                    "[--public]",
                    "[-i ID]",
                    ": error: the following arguments are required: -t/--title",
                ]
            ),
            None,  # expected_call
            id="no args",
        ),
    ],
)
def test_add_api_root(
    app, capsys, argv, raises, message, stdout, stderr, expected_call
):
    with (
        mock.patch("opentaxii.cli.persistence.app", app),
        mock.patch("sys.argv", [""] + argv),
        mock.patch.object(
            app.taxii_server.servers.taxii2.persistence.api,
            "add_api_root",
            autospec=True,
        ) as mock_add_api_root,
    ):
        with conditional_raises(raises) as exception:
            add_api_root()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)
        if expected_call is None:
            mock_add_api_root.assert_not_called()
        else:
            mock_add_api_root.assert_called_once_with(**expected_call)


@pytest.mark.parametrize(
    ["argv", "raises", "message", "stdout", "stderr", "expected_call"],
    [
        pytest.param(
            ["-r", str(API_ROOTS[0].id), "-t", "my new collection"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "api_root_id": str(API_ROOTS[0].id),
                "title": "my new collection",
                "description": None,
                "alias": None,
                "is_public": False,
                "is_public_write": False,
            },  # expected_call
            id="rootid, title only",
        ),
        pytest.param(
            [
                "-r",
                str(API_ROOTS[0].id),
                "-t",
                "my new collection",
                "-d",
                "my description",
            ],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "api_root_id": str(API_ROOTS[0].id),
                "title": "my new collection",
                "description": "my description",
                "alias": None,
                "is_public": False,
                "is_public_write": False,
            },  # expected_call
            id="rootid, title, description",
        ),
        pytest.param(
            [
                "-r",
                str(API_ROOTS[0].id),
                "-t",
                "my new collection",
                "-d",
                "my description",
                "-a",
                "my-alias",
            ],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "api_root_id": str(API_ROOTS[0].id),
                "title": "my new collection",
                "description": "my description",
                "alias": "my-alias",
                "is_public": False,
                "is_public_write": False,
            },  # expected_call
            id="rootid, title, description, alias",
        ),
        pytest.param(
            ["-r", str(API_ROOTS[0].id), "-t", "my new collection", "--public"],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "api_root_id": str(API_ROOTS[0].id),
                "title": "my new collection",
                "description": None,
                "alias": None,
                "is_public": True,
                "is_public_write": False,
            },  # expected_call
            id="rootid, titlei, public",
        ),
        pytest.param(
            [
                "-r",
                str(API_ROOTS[0].id),
                "-t",
                "my new collection",
                "--public-write",
            ],  # argv
            False,  # raises
            None,  # message
            "",  # stdout
            "",  # stderr
            {
                "api_root_id": str(API_ROOTS[0].id),
                "title": "my new collection",
                "description": None,
                "alias": None,
                "is_public": False,
                "is_public_write": True,
            },  # expected_call
            id="rootid, titlei, publicwrite",
        ),
        pytest.param(
            ["-r", "fake-uuid", "-t", "my new collection"],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-r {ROOTIDS}",
                    "-t TITLE",
                    "[-d DESCRIPTION]",
                    "[-a ALIAS]",
                    "[--public]",
                    "[--public-write]",
                    ": error: argument -r/--rootid: invalid choice: 'fake-uuid'",
                    "(choose from WRAPPED_ROOTIDS)",
                ]
            ),
            None,  # expected_call
            id="unknown api root",
        ),
        pytest.param(
            [],  # argv
            SystemExit,  # raises
            "2",  # message
            "",  # stdout
            "".join(  # stderr
                [
                    "usage:",
                    "[-h]",
                    "-r {ROOTIDS}",
                    "-t TITLE",
                    "[-d DESCRIPTION]",
                    "[-a ALIAS]",
                    "[--public]",
                    "[--public-write]",
                    ": error: the following arguments are required: -r/--rootid, -t/--title",
                ]
            ),
            None,  # expected_call
            id="no args",
        ),
    ],
)
def test_add_collection(
    app, db_api_roots, capsys, argv, raises, message, stdout, stderr, expected_call
):
    stderr = stderr.replace(
        "WRAPPED_ROOTIDS",
        ",".join([f"'{api_root.id}'" for api_root in db_api_roots]),
    )
    stderr = stderr.replace(
        "ROOTIDS",
        ",".join([str(api_root.id) for api_root in db_api_roots]),
    )
    with (
        mock.patch("opentaxii.cli.persistence.app", app),
        mock.patch("sys.argv", [""] + argv),
        mock.patch.object(
            app.taxii_server.servers.taxii2.persistence.api, "add_collection"
        ) as mock_add_collection,
    ):
        with conditional_raises(raises) as exception:
            add_collection()
        if raises:
            assert str(exception.value) == message
        captured = capsys.readouterr()
        assert_str_equal_no_formatting(captured.out, stdout)
        assert_str_equal_no_formatting(captured.err, stderr)
        if expected_call is None:
            mock_add_collection.assert_not_called()
        else:
            mock_add_collection.assert_called_once_with(**expected_call)


def test_job_cleanup(app, capsys):
    with (
        mock.patch("opentaxii.cli.persistence.app", app),
        mock.patch.object(
            app.taxii_server.servers.taxii2.persistence.api,
            "job_cleanup",
            return_value=2,
        ) as mock_cleanup,
    ):
        job_cleanup()
        mock_cleanup.assert_called_once_with()
        captured = capsys.readouterr()
        assert captured.out == "2 removed\n"
        assert captured.err == ""
