========
Accounts
========

Accounts can be created with CLI commands or with custom code talking to a specific Persistent API implementation/backend.

Manual commands
===============

.. code-block:: shell

    opentaxii-create-account --username <username> --password <pass> --admin

    # Update password
    opentaxii-update-account --username <username> --field password --value <pass>

    # Set admin
    opentaxii-update-account --username <username> --field admin --value yes
    # Reset admin
    opentaxii-update-account --username <username> --field admin --value no

Sync data
=========

.. code-block:: yaml

    accounts:
    - username: admin
        password: admin
        is_admin: yes