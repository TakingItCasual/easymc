from ec2mc import consts
from ec2mc.utils import aws
from ec2mc.utils.threader import Threader

def probe_regions():
    """return elastic IP addresses from whitelisted regions

    Requires ec2:DescribeAddresses permission.
    """
    threader = Threader()
    for region in consts.REGIONS:
        threader.add_thread(probe_region, (region,))
    region_addresses = threader.get_results(return_dict=True)

    return [{'region': region, **address}
        for region, addresses in region_addresses.items()
        for address in addresses]


def probe_region(region):
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
            address_info['instance_id'] = address['InstanceId']
        region_addresses.append(address_info)

    return sorted(region_addresses, key=lambda k: k['ip'])
