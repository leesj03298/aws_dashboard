# vpcdash/views.py

import boto3
from django.shortcuts import render

def vpc_list(request):
    ec2 = boto3.client('ec2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']  

    vpcs = []
    vpc_data = ec2.describe_vpcs()['Vpcs']
    igw_data = ec2.describe_internet_gateways()['InternetGateways']

    # IGW 연결된 VPC ID 추출
    igw_attached_vpc_ids = set()
    for igw in igw_data:
        for attachment in igw.get('Attachments', []):
            if attachment['State'] == 'available':
                igw_attached_vpc_ids.add(attachment['VpcId'])

    for vpc in vpc_data:
        tags = {t['Key']: t['Value'] for t in vpc.get('Tags', [])}
        vpcs.append({
            'account_id': account_id, 
            'id': vpc['VpcId'],
            'name': tags.get('Name', ''),
            'cidr': vpc['CidrBlock'],
            'state': vpc['State'],
            'has_igw': vpc['VpcId'] in igw_attached_vpc_ids,
            'tags': tags
        })

    return render(request, 'vpcdash/vpc_list.html', {'vpcs': vpcs})
