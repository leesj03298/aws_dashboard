from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_instances(session, account_id, account_name):
    ec2 = session.client('ec2', region_name='ap-northeast-2')
    reservations = ec2.describe_instances()['Reservations']

    rows = []
    for res in reservations:
        for inst in res['Instances']:
            instance_id = inst['InstanceId']
            instance_type = inst['InstanceType']
            state = inst['State']['Name']
            vpc_id = inst.get('VpcId', '')
            subnet_id = inst.get('SubnetId', '')
            private_ip = inst.get('PrivateIpAddress', '')
            tags = {t['Key']: t['Value'] for t in inst.get('Tags', [])}
            name = tags.get('Name', '')

            rows.append({
                'account_id': account_id,
                'name': name,
                'id': instance_id,
                'type': instance_type,
                'state': state,
                'vpc_id': vpc_id,
                'subnet_id': subnet_id,
                'private_ip': private_ip,
                'tags': tags,
            })

    return rows


def ec2_list(request):
    instances = with_all_accounts(fetch_instances)

    # ✅ 정렬 기준: VPC ID → Instance ID
    instances.sort(key=lambda x: (x['vpc_id'], x['id']))

    return render(request, 'ec2dash/ec2_list.html', {
        'instances': instances
    })
