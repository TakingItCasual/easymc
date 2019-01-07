from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils import pem
from ec2mc.utils.base_classes import ComponentSetup
from ec2mc.utils.threader import Threader

class SSHKeyPairSetup(ComponentSetup):

    def __init__(self, _):
        self._pem_file = consts.RSA_KEY_PEM.name
        self._key_pair_name = consts.RSA_KEY_PEM.stem


    def check_component(self):
        """determine which regions need namespace EC2 key pair created

        Returns:
            dict: Which regions namespace EC2 key pair exists in.
                Region name (str/None): Public key fingerprint, if pair exists.
        """
        threader = Threader()
        for region in consts.REGIONS:
            threader.add_thread(
                self._region_namespace_key_fingerprint, (region,))
        return threader.get_results(return_dict=True)


    def notify_state(self, fingerprint_regions):
        aws_fingerprints = [fp for fp in fingerprint_regions.values()
            if fp is not None]

        total_regions = len(consts.REGIONS)
        existing = len(aws_fingerprints)
        print(f"EC2 key pair {self._key_pair_name} exists in {existing} of "
            f"{total_regions} AWS regions.")

        if len(set(aws_fingerprints)) > 1:
            print("Warning: Differing EC2 key pairs found.")
            print("  Please delete EC2 key pairs and reupload.")
        if consts.RSA_KEY_PEM.is_file() and aws_fingerprints:
            if pem.local_key_fingerprint() not in aws_fingerprints:
                print("Warning: Local RSA key does not match EC2 key pair(s).")
        elif aws_fingerprints:
            print("Warning: Local RSA .pem key not found.")


    def upload_component(self, fingerprint_regions):
        """create namespace EC2 key pair in each whitelisted AWS region

        Args:
            fingerprint_regions (dict): See what check_component returns.
        """
        aws_fingerprints = [fp for fp in fingerprint_regions.values()
            if fp is not None]

        if consts.RSA_KEY_PEM.is_file():
            pub_key_bytes = pem.pem_to_public_key()
            print(f"Using existing {self._pem_file} file for EC2 key pair(s).")
        # If SSH key pair doesn't exist in any regions, create a new one
        elif not aws_fingerprints:
            pub_key_bytes = pem.generate_rsa_key_pair()
            print(f"Generating new {self._pem_file} file for EC2 key pair(s).")
        # No private key file, and there are existing EC2 key pairs
        else:
            halt.err(f"RSA private key file {self._pem_file} not found.",
                "  Additional pairs must be created from same private key.")

        if len(set(aws_fingerprints)) > 1:
            print("Warning: Differing EC2 key pairs found.")
        local_key_fingerprint = pem.local_key_fingerprint()
        if local_key_fingerprint not in aws_fingerprints and aws_fingerprints:
            halt.err("Local key fingerprint doesn't match any EC2 key pair.")

        threader = Threader()
        for region in fingerprint_regions:
            if fingerprint_regions[region] is None:
                threader.add_thread(
                    self._create_region_key_pair, (region, pub_key_bytes))
        created_pair_fingerprints = threader.get_results()

        if created_pair_fingerprints:
            print(f"EC2 key pair {self._key_pair_name} created in "
                f"{len(created_pair_fingerprints)} AWS region(s).")
        else:
            print(f"EC2 key pair {self._key_pair_name} "
                "already present in whitelisted region(s).")


    def delete_component(self):
        """remove namespace EC2 key pair from each whitelisted AWS region"""
        threader = Threader()
        for region in consts.REGIONS:
            threader.add_thread(self._delete_region_key_pair, (region,))
        deleted_key_pairs = threader.get_results()

        if any(deleted_key_pairs):
            print(f"EC2 key pair {self._key_pair_name} "
                "deleted from whitelisted AWS region(s).")
        else:
            print("No EC2 key pairs to delete.")


    def _region_namespace_key_fingerprint(self, region):
        """return key fingerprint if region has namespace EC2 key pair"""
        key_pairs = aws.ec2_client(region).describe_key_pairs(Filters=[
            {'Name': "key-name", 'Values': [self._key_pair_name]}
        ])['KeyPairs']
        if key_pairs:
            return key_pairs[0]['KeyFingerprint']
        return None


    def _create_region_key_pair(self, region, public_key_bytes):
        """create EC2 key pair in region and return public key fingerprint"""
        return aws.ec2_client(region).import_key_pair(
            KeyName=self._key_pair_name,
            PublicKeyMaterial=public_key_bytes
        )['KeyFingerprint']


    def _delete_region_key_pair(self, region):
        """delete namespace EC2 key pair from region"""
        if self._region_namespace_key_fingerprint(region) is not None:
            aws.ec2_client(region).delete_key_pair(KeyName=self._key_pair_name)
            return True
        return False


    @classmethod
    def blocked_actions(cls, sub_command):
        cls.describe_actions = ["ec2:DescribeKeyPairs"]
        cls.upload_actions = ["ec2:ImportKeyPair"]
        cls.delete_actions = ["ec2:DeleteKeyPair"]
        return super().blocked_actions(sub_command)
