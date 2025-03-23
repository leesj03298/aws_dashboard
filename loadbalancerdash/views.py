import boto3
from django.shortcuts import render
from collections import defaultdict

def loadbalancer_list(request):
    elbv2 = boto3.client('elbv2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    response = elbv2.describe_load_balancers()
    lb_groups = []

    for lb in response['LoadBalancers']:
        lb_arn = lb['LoadBalancerArn']
        lb_name = lb['LoadBalancerName']
        lb_type = lb['Type']
        scheme = lb['Scheme']
        vpc_id = lb.get('VpcId', '')
        dns = lb.get('DNSName', '')
        tags_response = elbv2.describe_tags(ResourceArns=[lb_arn])
        tags = {t['Key']: t['Value'] for t in tags_response['TagDescriptions'][0].get('Tags', [])}
        name = tags.get('Name', lb_name)

        # 리스너 정보
        listeners = []
        try:
            listener_response = elbv2.describe_listeners(LoadBalancerArn=lb_arn)
            for listener in listener_response['Listeners']:
                port = listener.get('Port')
                protocol = listener.get('Protocol')
                tg_arns = [a['TargetGroupArn'] for a in listener.get('DefaultActions', []) if 'TargetGroupArn' in a]
                target_group = tg_arns[0].split('/')[-2] if tg_arns else ''
                listeners.append({
                    'port': port,
                    'protocol': protocol,
                    'target_group': target_group
                })
        except Exception:
            continue

        lb_groups.append({
            'account_id': account_id,
            'name': name,
            'id': lb['LoadBalancerArn'].split('/')[-1],
            'type': lb_type,
            'scheme': scheme,
            'vpc_id': vpc_id,
            'dns': dns,
            'tags': tags,
            'listeners': listeners,
            'rowspan': len(listeners) or 1
        })

    # VPC ID 정렬
    lb_groups.sort(key=lambda x: x['vpc_id'])

    return render(request, 'loadbalancerdash/loadbalancer_list.html', {
        'loadbalancers': lb_groups
    })
