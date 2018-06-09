import os
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ec2mc import config
from ec2mc import update_template
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.threader import Threader

class SSHKeyPairSetup(update_template.BaseClass):

    def verify_component(self, _):
        """determine which regions need Namespace RSA key pairs created

        Returns:
            dict: Which regions Namespace EC2 key pair exists in.
                Region name (str/None): Public key fingerprint, if pair exists.
        """

        self.pem_file = os.path.basename(config.RSA_PRIV_KEY_PEM)
        self.key_pair_name = os.path.splitext(self.pem_file)[0]

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(
                self.region_namespace_key_fingerprint, (region,))
        return threader.get_results(return_dict=True)


    def notify_state(self, fingerprint_regions):
        aws_fingerprints = [fp for fp in fingerprint_regions.values()
            if fp is not None]

        total_regions = str(len(aws.get_regions()))
        existing = str(len(aws_fingerprints))
        print("EC2 key pair " + self.key_pair_name + " exists in " + existing +
            " of " + total_regions + " AWS regions.")

        if len(set(aws_fingerprints)) > 1:
            print("Warning: Differing EC2 key pairs found.")
        if os.path.isfile(config.RSA_PRIV_KEY_PEM) and aws_fingerprints:
            with open(config.RSA_PRIV_KEY_PEM, encoding="utf-8") as f:
                local_key_fingerprint = public_key_fingerprint(f.read())
            if local_key_fingerprint not in aws_fingerprints:
                print("Warning: Local key fingerprint doesn't match any "
                    "EC2 key pair.")
        elif aws_fingerprints:
            print("Warning: No local key found, despite existance of "
                "EC2 key pair(s).")


    def upload_component(self, fingerprint_regions):
        """create Namespace RSA key pairs in all AWS regions

        Args:
            fingerprint_regions (dict): See what verify_component returns.
        """

        aws_fingerprints = [fp for fp in fingerprint_regions.values()
            if fp is not None]

        if os.path.isfile(config.RSA_PRIV_KEY_PEM):
            with open(config.RSA_PRIV_KEY_PEM, encoding="utf-8") as f:
                priv_key_str = f.read()
            pub_key_bytes = pem_to_public_key(priv_key_str)
        # If SSH key pair doesn't exist in any regions, create a new one
        elif not aws_fingerprints:
            priv_key_str, pub_key_bytes = generate_rsa_key_pair()
            with open(config.RSA_PRIV_KEY_PEM, "w", encoding="utf-8") as f:
                f.write(priv_key_str)
        # No private key file, and there are existing EC2 key pairs
        else:
            halt.err("RSA private key file " + self.pem_file + " not found.",
                "  Additional pairs must be created from same private key.")

        if len(set(aws_fingerprints)) > 1:
            print("Warning: Differing EC2 key pairs found.")
        local_key_fingerprint = public_key_fingerprint(priv_key_str)
        if local_key_fingerprint not in aws_fingerprints and aws_fingerprints:
            halt.err("Local key fingerprint doesn't match any EC2 key pair.")

        threader = Threader()
        for region in fingerprint_regions:
            if fingerprint_regions[region] is None:
                threader.add_thread(
                    self.create_region_key_pair, (region, pub_key_bytes))
        created_pair_fingerprints = threader.get_results()

        if created_pair_fingerprints:
            print("EC2 key pair " + self.key_pair_name + " created in " +
                str(len(created_pair_fingerprints)) + " AWS region(s).")
        else:
            print("EC2 key pair " + self.key_pair_name +
                " already present in all regions.")


    def delete_component(self):
        """remove Namespace RSA key pairs from all AWS regions"""

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(self.delete_region_key_pair, (region,))
        deleted_key_pairs = threader.get_results()

        if any(deleted_key_pairs):
            print("EC2 key pair " + self.key_pair_name +
                " deleted from all AWS regions.")
        else:
            print("No EC2 key pairs to delete.")


    def region_namespace_key_fingerprint(self, region):
        """return key fingerprint if region has Namespace RSA key pair"""
        key_pairs = aws.ec2_client(region).describe_key_pairs(Filters=[{
            "Name": "key-name",
            "Values": [self.key_pair_name]
        }])["KeyPairs"]
        if key_pairs:
            return key_pairs[0]["KeyFingerprint"]
        return None


    def create_region_key_pair(self, region, public_key_bytes):
        """create EC2 key pair in region and return public key fingerprint"""
        return aws.ec2_client(region).import_key_pair(
            KeyName=self.key_pair_name,
            PublicKeyMaterial=public_key_bytes
        )["KeyFingerprint"]


    def delete_region_key_pair(self, region):
        """delete SSH key pair from region"""
        if self.region_namespace_key_fingerprint(region) is not None:
            aws.ec2_client(region).delete_key_pair(KeyName=self.key_pair_name)
            return True
        return False


    def blocked_actions(self, sub_command):
        self.describe_actions = ["ec2:DescribeKeyPairs"]
        self.upload_actions = ["ec2:ImportKeyPair"]
        self.delete_actions = ["ec2:DeleteKeyPair"]
        return super().blocked_actions(sub_command)


def generate_rsa_key_pair():
    """generate and return RSA private/public key pair

    Returns:
        tuple:
            str: Private key string
            str: Public key bytes
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

    # Get public key in OpenSSH format
    public_key_bytes = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    return (private_key_str, public_key_bytes)


def pem_to_public_key(pem_str, der_encoded=False):
    """convert pem RSA private key string to public key bytes"""
    try:
        private_key = serialization.load_pem_private_key(
            pem_str.encode("utf-8"),
            password=None,
            backend=default_backend()
        )
    except ValueError:
        halt.err(config.RSA_PRIV_KEY_PEM + " not a valid RSA private key.")

    if der_encoded is True:
        return private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return private_key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )


def public_key_fingerprint(pem_str):
    """get private key's public key's fingerprint in AWS's format"""
    public_key_der_bytes = pem_to_public_key(pem_str, der_encoded=True)
    md5_digest = hashlib.md5(public_key_der_bytes).hexdigest()
    return ":".join(a + b for a, b in zip(md5_digest[::2], md5_digest[1::2]))
