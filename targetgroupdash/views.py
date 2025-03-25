from django.shortcuts import render
from common.aws_multi import with_all_accounts
from collections import Counter

def fetch_target_groups(session, account_id, selected_vpc_id=None):
    elbv2 = session.client('elbv2', region_name='ap-northeast-2')
    tg_list = elbv2.describe_target_groups()['TargetGroups']

    result = []
    for tg in tg_list:
        vpc_id = tg.get('VpcId', '')
        if selected_vpc_id and vpc_id != selected_vpc_id:
            continue

        tg_arn = tg['TargetGroupArn']
        name = tg['TargetGroupName']
        protocol = tg.get('Protocol', '')
        port = tg.get('Port', '')
        target_type = tg.get('TargetType', '')
        health = tg.get('HealthCheckProtocol', '') + ' ' + tg.get('HealthCheckPath', '')
        tags_resp = elbv2.describe_tags(ResourceArns=[tg_arn])
        tags = {t['Key']: t['Value'] for t in tags_resp['TagDescriptions'][0].get('Tags', [])}
        tag_name = tags.get('Name', name)

        # 대상 상태 요약
        health_desc = elbv2.describe_target_health(TargetGroupArn=tg_arn)
        targets = health_desc.get('TargetHealthDescriptions', [])
        status_counts = Counter([t['TargetHealth']['State'] for t in targets])
        status_summary = ', '.join(f"{k}: {v}" for k, v in status_counts.items())

        result.append({
            'account_id': account_id,
            'name': tag_name,
            'vpc_id': vpc_id,
            'protocol': protocol,
            'port': port,
            'target_type': target_type,
            'health_check': health,
            'target_count': len(targets),
            'target_status': status_summary,
            'tags': tags
        })

    return result

def targetgroup_list(request):
    selected_account_id = request.GET.get('account_id')
    selected_vpc_id = request.GET.get('vpc_id')

    def fetch(session, account_id, account_name):
        if selected_account_id and account_id != selected_account_id:
            return []
        return fetch_target_groups(session, account_id, selected_vpc_id)

    target_groups = with_all_accounts(fetch)
    target_groups.sort(key=lambda x: (x['vpc_id'], x['name']))

    account_ids = sorted({tg['account_id'] for tg in target_groups})
    vpc_ids = sorted({tg['vpc_id'] for tg in target_groups})

    return render(request, 'targetgroupdash/targetgroup_list.html', {
        'target_groups': target_groups,
        'account_ids': account_ids,
        'vpc_ids': vpc_ids,
        'selected_account_id': selected_account_id,
        'selected_vpc_id': selected_vpc_id,
    })
