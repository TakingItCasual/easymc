from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils import aws
from ec2mc.utils.threader import Threader
from ec2mc.validate import validate_perms

class ListAddresses(CommandBase):

    def main(self, _):
        """list elastic IP addresses (and IDs of associated instances)"""
        regions = consts.REGIONS
        all_addresses = self.find_addresses(regions)

        print("")
        if not all_addresses:
            print("No Namespace elastic IP addresses found.")

        for region in regions:
            addresses = [address for address in all_addresses
                if address['region'] == region]
            if not addresses:
                continue

            print(f"{region}: {len(addresses)} address(es) found:")
            for address in addresses:
                if 'instance_id' in address:
                    print(f"  {address['ip']} ({address['instance_id']})")
                elif address['associated'] is True:
                    print(f"  {address['ip']} (unknown association)")
                else:
                    print(f"  {address['ip']} (not associated)")


    @classmethod
    def find_addresses(cls, regions):
        """return elastic IP addresses from all/whitelisted regions"""
        threader = Threader()
        for region in regions:
            threader.add_thread(cls.region_addresses, (region,))
        region_addresses = threader.get_results(return_dict=True)

        all_addresses = []
        for region, addresses in region_addresses.items():
            for address in addresses:
                all_addresses.append({
                    'region': region,
                    **address
                })

        return all_addresses


    @staticmethod
    def region_addresses(region):
        """return elastic IP addresses in region"""
        ec2_client = aws.ec2_client(region)
        addresses = ec2_client.describe_addresses(Filters=[
            {'Name': "domain", 'Values': ["vpc"]},
            {'Name': "tag:Namespace", 'Values': [consts.NAMESPACE]}
        ])['Addresses']

        region_addresses = []
        for address in addresses:
            to_append = {
                'ip': address['PublicIp'],
                'associated': True
            }
            if 'InstanceId' in address:
                to_append['instance_id'] = address['InstanceId']
            elif 'AssociationId' not in address:
                to_append['associated'] = False
            region_addresses.append(to_append)

        return sorted(region_addresses, key=lambda k: k['ip'])


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeRegions",
            "ec2:DescribeAddresses"
        ])
