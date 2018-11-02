import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ec2mc import consts
from ec2mc.utils import halt

def generate_rsa_key_pair() -> bytes:
    """generate RSA private/public key pair, save private, return public

    Returns:
        bytes: Public key bytes
    """
    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get private key string in PEM container format
    private_key_pem_str = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    consts.RSA_KEY_PEM.write_text(private_key_pem_str, encoding="utf-8")

    # Return public key bytes in OpenSSH format
    return private_key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )


def pem_to_public_key(der_encoded: bool=False) -> bytes:
    """convert pem RSA private key string to public key bytes"""
    pem_str = consts.RSA_KEY_PEM.read_text(encoding="utf-8")

    try:
        private_key = serialization.load_pem_private_key(
            pem_str.encode("utf-8"),
            password=None,
            backend=default_backend()
        )
    except ValueError:
        halt.err(f"{consts.RSA_KEY_PEM} not a valid RSA private key.")

    if der_encoded is True:
        return private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return private_key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )


def local_key_fingerprint() -> str:
    """get namespace private key's public key's fingerprint in AWS's format"""
    public_key_der_bytes = pem_to_public_key(der_encoded=True)
    md5_digest = hashlib.md5(public_key_der_bytes).hexdigest()
    return ":".join(a + b for a, b in zip(md5_digest[::2], md5_digest[1::2]))
