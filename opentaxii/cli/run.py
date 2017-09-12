
from opentaxii.cli import app
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import (
    serialization,
    hashes
)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from datetime import datetime

import structlog
import ssl
import socket
import os
import six
import sys

CERT_STORAGE_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CERT_FILE = os.path.join(CERT_STORAGE_DIR, "opentaxii-self-signed-cert.crt")
KEY_FILE = os.path.join(CERT_STORAGE_DIR, "opentaxii-self-signed-cert.key")

log = structlog.getLogger(__name__)


def run_in_dev_mode():
    app.run(port=9000)


def run_https_in_dev_mode():

    # Generate a self-signed key if one isn't here already
    if not os.path.isfile(CERT_FILE) or not os.path.isfile(KEY_FILE):

        log.warning(
             "Invalid or missing SSL Certificate or Private Key."
             " Creating new SSL certificate at {} and Private Key at {}"
             .format(CERT_FILE, KEY_FILE))

        # Create private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Write the key to the disk
        with open(KEY_FILE, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        # Generate the self signed certifiate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"NL"),
            x509.NameAttribute(
                NameOID.STATE_OR_PROVINCE_NAME,
                u"North Holland"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Amsterdam"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"EclecticIQ"),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                six.u(socket.gethostname())),
        ])
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime(2020, 7, 1)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
            # Sign our certificate with our private key
        ).sign(key, hashes.SHA256(), default_backend())

        # Write our certificate out to disk.
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
    else:
        log.info(
            "Using SSL certificate at {} and Private Key at {}"
            .format(CERT_FILE, KEY_FILE))

    # Set up the SSL configuration
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    # Run the application
    app.run(port=9000, ssl_context=context)
