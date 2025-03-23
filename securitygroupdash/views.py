import boto3
from django.shortcuts import render
from collections import defaultdict

def securitygroup_list(request):
    ec2 = boto3.client('ec2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    # ✅ GET 파라미터로부터 필터 값
    selected_vpc_id = request.GET.get('vpc_id')
    selected_direction = request.GET.get('direction')

    response = ec2.describe_security_groups()
    grouped_sgs = defaultdict(list)
    vpc_ids_set = set()

    for sg in response['SecurityGroups']:
        vpc_id = sg.get('VpcId', '')
        vpc_ids_set.add(vpc_id)

        # ✅ VPC ID 필터
        if selected_vpc_id and vpc_id != selected_vpc_id:
            continue

        tags = {t['Key']: t['Value'] for t in sg.get('Tags', [])}
        name = tags.get('Name') or sg.get('GroupName')

        base_info = {
            'account_id': account_id,
            'name': name,
            'group_id': sg['GroupId'],
            'vpc_id': vpc_id,
            'tags': tags,
        }

        # ✅ Inbound
        if not selected_direction or selected_direction == 'Inbound':
            for perm in sg.get('IpPermissions', []):
                grouped_sgs[sg['GroupId']].extend(
                    parse_permission(perm, base_info, 'Inbound')
                )

        # ✅ Outbound
        if not selected_direction or selected_direction == 'Outbound':
            for perm in sg.get('IpPermissionsEgress', []):
                grouped_sgs[sg['GroupId']].extend(
                    parse_permission(perm, base_info, 'Outbound')
                )

    # ✅ SG 병합 리스트 구성
    sg_groups = []
    for group_id, rules in grouped_sgs.items():
        if not rules:
            continue
        rules.sort(key=lambda r: (r['direction'], r['cidr'] or ''))
        sg_groups.append({
            'group_id': group_id,
            'rowspan': len(rules),
            'rules': rules,
        })

    # ✅ VPC 정렬
    sg_groups.sort(key=lambda g: g['rules'][0]['vpc_id'])

    # ✅ VPC 목록 전달
    vpc_ids = sorted(vpc_ids_set)

    return render(request, 'securitygroupdash/securitygroup_list.html', {
        'sg_groups': sg_groups,
        'vpc_ids': vpc_ids,
        'selected_vpc_id': selected_vpc_id,
        'selected_direction': selected_direction,
    })


def parse_permission(perm, base_info, direction):
    results = []
    ip_ranges = perm.get('IpRanges', [])
    ipv6_ranges = perm.get('Ipv6Ranges', [])
    sg_refs = perm.get('UserIdGroupPairs', [])

    port_from = perm.get('FromPort')
    port_to = perm.get('ToPort')
    protocol = perm.get('IpProtocol')

    if port_from is None and port_to is None:
        port_display = 'ALL'
    elif port_from == port_to:
        port_display = str(port_from)
    else:
        port_display = f"{port_from}-{port_to}"

    if protocol == '-1':
        protocol = 'ALL'

    for ip in ip_ranges:
        results.append({**base_info, 'direction': direction, 'protocol': protocol,
                        'port': port_display, 'cidr': ip.get('CidrIp'), 'desc': ip.get('Description', '')})
    for ip6 in ipv6_ranges:
        results.append({**base_info, 'direction': direction, 'protocol': protocol,
                        'port': port_display, 'cidr': ip6.get('CidrIpv6'), 'desc': ip6.get('Description', '')})
    for ref in sg_refs:
        results.append({**base_info, 'direction': direction, 'protocol': protocol,
                        'port': port_display, 'cidr': ref.get('GroupId'), 'desc': ref.get('Description', '')})
    return results
