==============
Authentication
==============

.. highlight:: sh

Overview
========

Authentication can be configured per service instance: ``authentication_required``
boolean service class field defines if the client needs to be
authenticated before accessing the service.

OpenTAXII implements session-less token-based authentication.

If authentication is required, OpenTAXII expects clients to obtain a token first and
send it as ``Authorization`` HTTP header value (formatted as ``Bearer TOKENVALUE``)
with every TAXII request.

To obtain a token, client sends a ``POST`` request with username and password to 
authentication service running by default on ``/management/auth``.

Request data can be a form-encoded string or a JSON dictionary with ``username`` and
``password`` fields::

    $ curl -d 'username=test&password=test' http://localhost:9000/management/auth

or::

    $ curl -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' http://localhost:9000/management/auth

A server will reply with a JSON dictionary that contains a token::

    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoxLCJleHAiOjE0Mjc2MzgyMjN9.oKd43j4KR1Ovu8zOtwFdeaKILys_kpl3fAiECclP7_4"
    }

To query a service with enabled authentication, pass the token in a value of ``Authorization`` HTTP header.
Example request using `Cabby library <http://github.com/Intelworks/cabby>`_ CLI command::

    (venv) $ taxii-poll \
                --path http://localhost:9000/services/poll-a \
                --collection collection-A \
                --header Authorization:'Bearer eyJleHAiOjE0MjY3OTMwOTYsImFsZyI6IkhTMjU2IiwiaWF0IjoxNDI2Nzg1ODk2fQ.eyJ1c2VyX2lkIjoxfQ.YsZIdbrU92dL8j5G8ydVAsdWHXtx371vC0POmXrS3W8'


Built-in implementation
=======================

Build-in Authentication API implementation uses
`JWT (JSON Web Token) <https://tools.ietf.org/html/draft-ietf-oauth-json-web-token-32>`_
to create the tokens.

Token TTL is set to 60 minutes.

Authentication API needs to be able to identify a client based on the token
(method :py:meth:`opentaxii.auth.api.OpenTAXIIAuthAPI.get_account` of the API). Built-in implementation
does that by encoding account ID inside the token.

.. rubric:: Next steps

Continue to :doc:`Public code-level APIs <public-apis>` page for the details about OpenTAXII APIs.

.. vim: set spell spelllang=en:

