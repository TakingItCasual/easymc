import os
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from ec2mc import config
from ec2mc import update_template
from ec2mc.utils import aws
from ec2mc.utils.threader import Threader

import pprint
pp = pprint.PrettyPrinter(indent=2)

class SSHKeyPairSetup(update_template.BaseClass):

    def verify_component(self, _):
        """determine which regions need Namespace RSA key pairs created

        Returns:
            dict: Which regions Namespace EC2 key pair exists in.
                Region name (str/None): Public key fingerprint, if pair exists.
        """

        self.key_pair_name = config.NAMESPACE
        self.pem_file = self.key_pair_name + ".pem"
        self.pem_file_path = config.CONFIG_DIR + self.pem_file

        threader = Threader()
        for region in aws.get_regions():
            threader.add_thread(
                self.region_namespace_key_fingerprint, (region,))
        return threader.get_results(return_dict=True)


    def notify_state(self, fingerprint_regions):
        total_regions = str(len(fingerprint_regions))
        existing = str(len([fp for fp in fingerprint_regions.values()
            if fp is not None]))
        print("EC2 key pair " + self.key_pair_name + " exists in " + existing +
            " of " + total_regions + " AWS regions.")


    def upload_component(self, fingerprint_regions):
        """create Namespace RSA key pairs in all AWS regions

        Args:
            fingerprint_regions (dict): See what verify_component returns.
        """

        all_regions = aws.get_regions()

        if os.path.isfile(self.pem_file_path):
            with open(self.pem_file_path, encoding="utf-8") as f:
                priv_key_str = f.read()
                pub_key_str = self.pem_to_public_key(priv_key_str)
        # If SSH key pair doesn't exist in any regions, create a new one
        elif not [fp for fp in fingerprint_regions.values() if fp is not None]:
            priv_key_str, pub_key_str = self.generate_rsa_key_pair()
            with open(self.pem_file_path, "w", encoding="utf-8") as f:
                f.write(priv_key_str)
        # No private key file, and there are existing EC2 key pairs
        else:
            halt.err(["RSA private key file " + self.pem_file + " not found.",
                "  Additional pairs must be created from same private key."])

        for region in fingerprint_regions:
            if fingerprint_regions[region] is None:
                self.create_region_key_pair(region, pub_key_str)


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


    def fingerprints_match(self, fingerprint_regions):
        """warn if EC2 key pair fingerprints differ from each other or .pem"""
        fingerprints = [fp for fp in fingerprint_regions.values()
            if fp is not None]
        if len(set(fingerprints)) > 1:
            print("Warning: EC2 key pair fingerprints not all equal.")


    def region_namespace_key_fingerprint(self, region):
        """return key fingerprint if region has Namespace RSA key pair"""
        key_pairs = aws.ec2_client(region).describe_key_pairs(Filters=[{
            "Name": "key-name",
            "Values": [self.key_pair_name]
        }])["KeyPairs"]
        if key_pairs:
            return key_pairs[0]["KeyFingerprint"]
        return None


    def create_region_key_pair(self, region, public_key_str):
        """create SSH key pair in region and return key fingerprint"""
        return aws.ec2_client(region).import_key_pair(
            KeyName=self.key_pair_name,
            PublicKeyMaterial=public_key_str.encode("utf-8")
        )["KeyFingerprint"]


    def delete_region_key_pair(self, region):
        """delete SSH key pair from region"""
        if self.region_namespace_key_fingerprint(region) is not None:
            aws.ec2_client(region).delete_key_pair(KeyName=self.key_pair_name)
            return True
        return False


    def generate_rsa_key_pair(self):
        """generate and return RSA private/public key pair strings

        Returns:
            tuple:
                str: Private key string
                str: Public key string
        """

        # generate private/public key pair
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048
        )

        # get public key in OpenSSH format
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        )

        # get private key in PEM container format
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        # decode to printable strings
        private_key_str = pem.decode("utf-8")
        public_key_str = public_key.decode("utf-8")

        return (private_key_str, public_key_str)


    def pem_to_public_key(self, pem_str):
        """converts pem RSA private key string to public key string"""
        return serialization.load_pem_private_key(
            pem_str.encode("utf-8"),
            password=None, 
            backend=default_backend()
        ).public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        ).decode("utf-8")


    def public_key_fingerprint(self, public_key_str):
        """return MD5 public key fingerprint (":" every 2 characters)"""
        md5digest = hashlib.md5(public_key_str).hexdigest()
        return ":".join(a+b for a,b in zip(md5digest[::2], md5digest[1::2]))


    def blocked_actions(self, sub_command):
        self.describe_actions = ["ec2:DescribeKeyPairs"]
        self.upload_actions = ["ec2:ImportKeyPair"]
        self.delete_actions = ["ec2:DeleteKeyPair"]
        return super().blocked_actions(sub_command)
