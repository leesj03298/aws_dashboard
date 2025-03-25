from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_subnets(session, account_id, selected_vpc_id=None):
    ec2 = session.client('ec2', region_name='ap-northeast-2')
    subnets = ec2.describe_subnets()['Subnets']

    rows = []
    for subnet in subnets:
        vpc_id = subnet['VpcId']
        if selected_vpc_id and vpc_id != selected_vpc_id:
            continue

        subnet_id = subnet['SubnetId']
        cidr = subnet['CidrBlock']
        az = subnet.get('AvailabilityZone', '')
        state = subnet.get('State', '')
        is_public = subnet.get('MapPublicIpOnLaunch', False)
        tags = {t['Key']: t['Value'] for t in subnet.get('Tags', [])}
        name = tags.get('Name', '')

        rows.append({
            'account_id': account_id,
            'name': name,
            'id': subnet_id,
            'vpc_id': vpc_id,
            'cidr': cidr,
            'az': az,
            'state': state,
            'public': is_public,
            'tags': tags,
        })

    return rows

def subnet_list(request):
    selected_account_id = request.GET.get('account_id')
    selected_vpc_id = request.GET.get('vpc_id')

    def fetch(session, account_id, account_name):
        if selected_account_id and account_id != selected_account_id:
            return []
        return fetch_subnets(session, account_id, selected_vpc_id)

    subnets = with_all_accounts(fetch)
    subnets.sort(key=lambda x: (x['vpc_id'], x['id']))

    account_ids = sorted({s['account_id'] for s in subnets})
    vpc_ids = sorted({s['vpc_id'] for s in subnets})

    return render(request, 'subnetdash/subnet_list.html', {
        'subnets': subnets,
        'account_ids': account_ids,
        'vpc_ids': vpc_ids,
        'selected_account_id': selected_account_id,
        'selected_vpc_id': selected_vpc_id,
    })