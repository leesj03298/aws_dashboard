from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_vpcs(session, account_id, account_name):
    ec2 = session.client('ec2', region_name='ap-northeast-2')
    vpcs = ec2.describe_vpcs()['Vpcs']
    igws = ec2.describe_internet_gateways()['InternetGateways']

    # VPC ID 기준으로 IGW 연결 여부 확인용 set
    igw_vpc_ids = {
        a['VpcId']
        for igw in igws
        for a in igw.get('Attachments', [])
        if a.get('State') == 'available'
    }

    rows = []
    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        cidr = vpc['CidrBlock']
        state = vpc['State']
        tags = {t['Key']: t['Value'] for t in vpc.get('Tags', [])}
        name = tags.get('Name', '')
        has_igw = vpc_id in igw_vpc_ids

        rows.append({
            'account_id': account_id,
            'name': name,
            'id': vpc_id,
            'cidr': cidr,
            'state': state,
            'has_igw': has_igw,
            'tags': tags
        })

    return rows


def vpc_list(request):
    vpcs = with_all_accounts(fetch_vpcs)

    # 정렬 (예: VPC ID 기준)
    vpcs.sort(key=lambda x: x['id'])

    return render(request, 'vpcdash/vpc_list.html', {
        'vpcs': vpcs
    })
