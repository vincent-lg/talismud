# Copyright 2018 Simon Davy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""SSL helpers to create self-signed certificates.

This file retains the original license from the example at
https://gist.github.com/bloodearnest/9017111a313777b9cce5
on which most of these functions are based.  However, they have been
extended to better fit TalisMUD's needs.

Functions:
    generate_self_signed_cert: generate a certificate and private key.
    save_cert: save the certificate and private key in two files.

"""

from datetime import datetime, timedelta
import ipaddress
import os
from pathlib import Path
import platform
from typing import Optional, Sequence, Tuple

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_self_signed_cert(hostname: str,
        ip_addresses: Optional[Sequence[ipaddress._BaseAddress]] = None,
        country: str = "FR", state: str = "None", locality: str = "Paris",
        organization: str = "TalisMUD") -> Tuple[bytes, bytes]:
    """
    Generate a self-signed certificate for a hostname.

    Args:
        hostname (str): the hostname to use in the certificate.
        ip_addresses (list, optional): the optional IP addresses.
        country (str, optional): the country to use for this certificate.
        state (str, optional): the state or province to use.
        locality (str, optional): the locality (city name).
        organization (str, optional): the organization to use.

    Returns:
        cert, key (bytes, bytes): the signed certificate and private key.

    """
    # Generate the private key
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend(),
    )

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname)
    ])

    # Include the hostname in the SAN
    alt_names = [x509.DNSName(hostname)]

    # Allow addressing by IP, for when you don't have real DNS
    if ip_addresses:
        for addr in ip_addresses:
            # OpenSSL wants DNSnames for ips...
            alt_names.append(x509.DNSName(addr))
            # ... whereas Golang's crypto/tls is stricter (needs IPAddresses)
            alt_names.append(x509.IPAddress(ipaddress.ip_address(addr)))

    san = x509.SubjectAlternativeName(alt_names)

    # path_len=0 means this cert can only sign itself, not other certs.
    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)

    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=10 * 365))
        .add_extension(basic_contraints, False)
        .add_extension(san, False)
        .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return cert_pem, key_pem

def save_cert(prefix: str, hostname: str,
        ip_addresses: Optional[Sequence[ipaddress._BaseAddress]] = None,
        country: str = "FR", state: str = "None", locality: str = "Paris",
        organization: str = "TalisMUD") -> Tuple[bytes, bytes]:
    """
    Generate and save a self-signed certificate.

    This will create two files: one containing the certificate, the other containing the private key.  These files will be stored in `prefix.cert` and `prefix.key` respectively.

    Args:
        prefix (str): the prefix to store the two files.
        hostname (str): the hostname to use to generate the certificate.
        ip_addresses (list, optional): the IP addresses.
        country (str, optional): the country to use for this certificate.
        state (str, optional): the state or province to use.
        locality (str, optional): the locality (city name).
        organization (str, optional): the organization to use.

    """
    cert, key = generate_self_signed_cert(hostname=hostname,
            ip_addresses=ip_addresses, country=country, state=state,
            locality=locality, organization=organization)

    # Save in two files
    cert_path = Path() / (prefix + ".cert")
    key_path = Path() / (prefix + ".key")
    parent = cert_path.parent

    # If the directory doesn't exist, create it
    if not parent.exists():
        parent.mkdir(mode=0o700)
        # On Windows only, hide the directory with a command (ugly hack)
        if platform.system() == "Windows":
            os.system(f"attrib +h {parent}")

    # Write both files
    with cert_path.open("wb") as cert_file:
        cert_file.write(cert)
    cert_path.chmod(0o600)
    with key_path.open("wb") as key_file:
        key_file.write(key)
    key_path.chmod(0o600)
