from ec2mc import consts
from ec2mc.utils.base_classes import CommandBase
from ec2mc.utils.find import find_addresses
from ec2mc.validate import validate_perms

class ListAddresses(CommandBase):

    def main(self, _):
        """list elastic IP addresses and their associations"""
        all_addresses = find_addresses.probe_regions()

        print("")
        if not all_addresses:
            print("No namespace elastic IP addresses found.")

        for region in consts.REGIONS:
            region_addresses = [address for address in all_addresses
                if address['region'] == region]
            if not region_addresses:
                continue

            print(f"{region}: {len(region_addresses)} address(es) found:")
            for address in region_addresses:
                if 'instance_name' in address:
                    print(f"  {address['ip']} ({address['instance_name']})")
                elif 'association_id' in address:
                    print(f"  {address['ip']} (unknown association)")
                else:
                    print(f"  {address['ip']} (not associated)")


    def blocked_actions(self, _):
        return validate_perms.blocked(actions=[
            "ec2:DescribeInstances",
            "ec2:DescribeAddresses"
        ])
