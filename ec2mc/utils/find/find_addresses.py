from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.utils.find import find_instances
from ec2mc.utils.threader import Threader

def main(elastic_ip_address):
    """attempt to return elastic IP address with specified IP

    Requires ec2:DescribeInstances and ec2:DescribeAddresses permissions.

    Halts if address with IP not found. This functionality is relied upon.
    """
    try:
        return next(address for address in probe_regions()
            if address['ip'] == elastic_ip_address)
    except StopIteration:
        halt.err("You do not possess the specified elastic IP address.")


def probe_regions():
    """return elastic IP addresses from whitelisted regions

    Requires ec2:DescribeInstances and ec2:DescribeAddresses permissions.
    """
    all_instances = find_instances.probe_regions()

    threader = Threader()
    for region in consts.REGIONS:
        threader.add_thread(_probe_region, (region, all_instances))
    region_addresses = threader.get_results(return_dict=True)

    return [{'region': region, **address}
        for region, addresses in region_addresses.items()
        for address in addresses]


def _probe_region(region, instances):
    """return elastic IP addresses in region

    Requires ec2:DescribeAddresses permission.
    """
    ec2_client = aws.ec2_client(region)
    addresses = ec2_client.describe_addresses(Filters=[
        {'Name': "domain", 'Values': ["vpc"]},
        {'Name': "tag:Namespace", 'Values': [consts.NAMESPACE]}
    ])['Addresses']

    region_addresses = []
    for address in addresses:
        address_info = {
            'allocation_id': address['AllocationId'],
            'ip': address['PublicIp']
        }
        if 'AssociationId' in address:
            address_info['association_id'] = address['AssociationId']
        if 'InstanceId' in address:
            for instance in instances:
                if (instance['id'] == address['InstanceId'] and
                        instance['region'] == region):
                    address_info['instance_name'] = instance['name']
                    break
        region_addresses.append(address_info)

    return sorted(region_addresses, key=lambda k: k['ip'])
