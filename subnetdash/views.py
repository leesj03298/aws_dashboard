import boto3
from django.shortcuts import render

def subnet_list(request):
    ec2 = boto3.client('ec2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    response = ec2.describe_subnets()
    subnets = []

    for sn in response['Subnets']:
        tags = {t['Key']: t['Value'] for t in sn.get('Tags', [])}
        subnets.append({
            'account_id': account_id,
            'id': sn['SubnetId'],
            'name': tags.get('Name', ''),
            'vpc_id': sn['VpcId'],
            'cidr': sn['CidrBlock'],
            'az': sn['AvailabilityZone'],
            'state': sn['State'],
            'public': sn['MapPublicIpOnLaunch'],
            'tags': tags,
        })

    return render(request, 'subnetdash/subnet_list.html', {'subnets': subnets})
