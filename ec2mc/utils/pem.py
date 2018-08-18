import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ec2mc import config
from ec2mc.utils import halt

def generate_rsa_key_pair():
    """generate RSA private/public key pair, save private, return public

    Returns:
        bytes: Public key bytes
    """
    # Generate private/public key pair
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get private key in PEM container format
    private_key_str = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    with open(config.RSA_PRIV_KEY_PEM, "w", encoding="utf-8") as f:
        f.write(private_key_str)

    # Get public key in OpenSSH format
    public_key_bytes = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    return public_key_bytes


def pem_to_public_key(der_encoded=False):
    """convert pem RSA private key string to public key bytes"""
    with open(config.RSA_PRIV_KEY_PEM, encoding="utf-8") as f:
        pem_str = f.read()

    try:
        private_key = serialization.load_pem_private_key(
            pem_str.encode("utf-8"),
            password=None,
            backend=default_backend()
        )
    except ValueError:
        halt.err(f"{config.RSA_PRIV_KEY_PEM} not a valid RSA private key.")

    if der_encoded is True:
        return private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return private_key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )


def local_key_fingerprint():
    """get Namespace private key's public key's fingerprint in AWS's format"""
    public_key_der_bytes = pem_to_public_key(der_encoded=True)
    md5_digest = hashlib.md5(public_key_der_bytes).hexdigest()
    return ":".join(a + b for a, b in zip(md5_digest[::2], md5_digest[1::2]))
