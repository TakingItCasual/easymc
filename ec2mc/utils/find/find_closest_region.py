from timeit import default_timer as timer

from ec2mc.utils import aws
from ec2mc.utils.threader import Threader

def main(regions):
    """repeatedly use ec2:DescribeRegions action to estimate closest region"""
    ping_num = 50

    threader = Threader()
    for region in regions:
        ec2_client = aws.ec2_client_no_validate(region)
        for _ in range(ping_num):
            threader.add_thread(get_region_latency, (ec2_client,))
    latencies = threader.get_results()

    latencies_for_regions = []
    for i, region in enumerate(regions):
        region_latencies = sorted(latencies[i*ping_num:(i+1)*ping_num])
        region_latencies = region_latencies[ping_num//5:-ping_num//5]
        region_latency = sum(region_latencies) / len(region_latencies)
        latencies_for_regions.append((region, region_latency))

    latencies_for_regions.sort(key=lambda tup: tup[1])
    return latencies_for_regions[0][0]


def get_region_latency(ec2_client):
    """get millisecond latency of region endpoint"""
    start_time = timer()
    ec2_client.describe_regions()
    end_time = timer()
    return end_time - start_time
