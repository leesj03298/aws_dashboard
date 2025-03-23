#from django.shortcuts import render

# Create your views here.

# ec2dash/views.py

import boto3
from django.shortcuts import render

def ec2_list(request):
    ec2 = boto3.client('ec2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']  # ✅ Account ID 조회
    res = ec2.describe_instances()

    instances = []
    

    selected_state = request.GET.get('state')
    selected_az = request.GET.get('az')

    for r in res['Reservations']:
        for inst in r['Instances']:
            tags = {t['Key']: t['Value'] for t in inst.get('Tags', [])}
            instance = {
                'account_id': account_id,
                'name': tags.get('Name', ''),
                'id': inst['InstanceId'],
                'type': inst['InstanceType'],
                'state': inst['State']['Name'],
                'az': inst['Placement']['AvailabilityZone'],
                'vpc': inst.get('VpcId', '—'),
                'subnet': inst.get('SubnetId', '—'),
                'private_ip': inst.get('PrivateIpAddress', '—'),

                'tags': {t['Key']: t['Value'] for t in inst.get('Tags', [])},
            }

            # 필터 조건 체크
            if selected_state and instance['state'] != selected_state:
                continue
            if selected_az and instance['az'] != selected_az:
                continue

            instances.append(instance)

    return render(request, 'ec2dash/ec2_list.html', {
        'instances': instances
    })
