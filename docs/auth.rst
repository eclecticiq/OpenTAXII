==============
Authentication
==============

.. highlight:: sh

Services Authentication (Client-side)
=====================================

Authentication can be configured per service instance with ``authentication_required``. This is a boolean service class field which defines if the client needs to be
authenticated before accessing the service.

.. note::
	OpenTAXII supports session-less token-based authentication as primary method of authentication with fallback to Basic authentication.

If authentication is required, OpenTAXII expects clients to obtain a token first and
send it as ``Authorization`` HTTP header value (formatted as ``Bearer TOKENVALUE``)
with every TAXII request.

To obtain a token, client sends a ``POST`` request with username and password to 
authentication service running on ``/management/auth``.

Request data can be a form-encoded string or a JSON dictionary with ``username`` and
``password`` fields::

    (venv) $ curl -d 'username=test&password=test' http://localhost:9000/management/auth

or::

    (venv) $ curl -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' http://localhost:9000/management/auth

A server will reply with a JSON dictionary that contains a token. For example::

    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoxLCJleHAiOjE0Mjc2MzgyMjN9.oKd43j4KR1Ovu8zOtwFdeaKILys_kpl3fAiECclP7_4"
    }

To query a service with authentication enabled, pass the token in a value of ``Authorization`` HTTP header.
Example request using `Cabby library <http://github.com/eclecticiq/cabby>`_ CLI command::

    # using raw HTTP header
    (venv) $ taxii-poll \
                --path http://localhost:9000/services/poll-a \
                --collection collection-A \
                --header Authorization:'Bearer eyJleHAiOjE0MjY3OTMwOTYsImFsZyI6IkhTMjU2IiwiaWF0IjoxNDI2Nzg1ODk2fQ.eyJ1c2VyX2lkIjoxfQ.YsZIdbrU92dL8j5G8ydVAsdWHXtx371vC0POmXrS3W8'

    # using JWT support in Cabby
    (venv) $ taxii-poll \
                --host localhost:9000 \
                --path /services/poll-a \
                --collection collection-A \
                --username test \
                --password test \
                --jwt-auth /management/auth

An alternative to that is to use Basic Authentication header: client sends username/password formatted as Basic Authentication header with every TAXII request, OpenTAXII decodes it and passes username/password pair to Auth API for authentication.

Authentication Implementation
=============================

The build-in Authentication API implementation uses
`JWT (JSON Web Token) <https://tools.ietf.org/html/draft-ietf-oauth-json-web-token-32>`_
to create tokens.

Token TTL is set to 60 minutes.

Authentication API needs to be able to identify a client based on the token
(method :py:meth:`opentaxii.auth.api.OpenTAXIIAuthAPI.get_account` of the API). The built-in implementation
does that by encoding account ID inside the token.

.. rubric:: Next steps

Continue to :doc:`Public code-level APIs <public-apis>` page for the details about OpenTAXII APIs.

.. vim: set spell spelllang=en:

