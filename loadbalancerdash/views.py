from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_load_balancers(session, account_id, selected_vpc_id=None):
    elbv2 = session.client('elbv2', region_name='ap-northeast-2')
    lbs = elbv2.describe_load_balancers()['LoadBalancers']

    lb_groups = []
    for lb in lbs:
        vpc_id = lb.get('VpcId', '')
        if selected_vpc_id and vpc_id != selected_vpc_id:
            continue
        lb_arn = lb['LoadBalancerArn']
        lb_name = lb['LoadBalancerName']
        lb_type = lb['Type']
        scheme = lb['Scheme']
        vpc_id = lb.get('VpcId', '')
        dns = lb.get('DNSName', '')

        # 태그 가져오기
        tags_response = elbv2.describe_tags(ResourceArns=[lb_arn])
        tags = {t['Key']: t['Value'] for t in tags_response['TagDescriptions'][0].get('Tags', [])}
        name = tags.get('Name', lb_name)

        # 리스너 수집
        listeners = []
        try:
            response = elbv2.describe_listeners(LoadBalancerArn=lb_arn)
            for listener in response['Listeners']:
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
            'id': lb_arn.split('/')[-1],
            'type': lb_type,
            'scheme': scheme,
            'vpc_id': vpc_id,
            'dns': dns,
            'tags': tags,
            'listeners': listeners,
            'rowspan': len(listeners) or 1
        })

    return lb_groups

def loadbalancer_list(request):
    selected_account_id = request.GET.get('account_id')
    selected_vpc_id = request.GET.get('vpc_id')

    def fetch(session, account_id, account_name):
        if selected_account_id and account_id != selected_account_id:
            return []
        return fetch_load_balancers(session, account_id, selected_vpc_id)

    loadbalancers = with_all_accounts(fetch)
    loadbalancers.sort(key=lambda x: x['vpc_id'])

    # 필터 select용 unique 목록 추출
    account_ids = sorted({lb['account_id'] for lb in loadbalancers})
    vpc_ids = sorted({lb['vpc_id'] for lb in loadbalancers})

    return render(request, 'loadbalancerdash/loadbalancer_list.html', {
        'loadbalancers': loadbalancers,
        'account_ids': account_ids,
        'vpc_ids': vpc_ids,
        'selected_account_id': selected_account_id,
        'selected_vpc_id': selected_vpc_id,
    })
