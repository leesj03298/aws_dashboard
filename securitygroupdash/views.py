from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_security_groups(session, account_id, selected_vpc_id=None):
    ec2 = session.client('ec2', region_name='ap-northeast-2')
    response = ec2.describe_security_groups()
    grouped_sgs = {}

    for sg in response['SecurityGroups']:
        vpc_id = sg.get('VpcId', '')
        if selected_vpc_id and vpc_id != selected_vpc_id:
            continue

    for sg in response['SecurityGroups']:
        tags = {t['Key']: t['Value'] for t in sg.get('Tags', [])}
        name = tags.get('Name') or sg.get('GroupName')

        base_info = {
            'account_id': account_id,
            'name': name,
            'group_id': sg['GroupId'],
            'vpc_id': sg.get('VpcId', ''),
            'tags': tags,
        }

        rules = []

        for perm in sg.get('IpPermissions', []):
            rules.extend(parse_permission(perm, base_info, 'Inbound'))

        for perm in sg.get('IpPermissionsEgress', []):
            rules.extend(parse_permission(perm, base_info, 'Outbound'))

        if rules:
            grouped_sgs[sg['GroupId']] = rules

    sg_groups = []
    for group_id, rules in grouped_sgs.items():
        rules.sort(key=lambda r: (r['direction'], r['cidr'] or ''))
        sg_groups.append({
            'group_id': group_id,
            'rowspan': len(rules),
            'rules': rules,
        })

    return sg_groups


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

def securitygroup_list(request):
    selected_vpc_id = request.GET.get('vpc_id')
    selected_account_id = request.GET.get('account_id')

    def fetch(session, account_id, account_name):
        if selected_account_id and account_id != selected_account_id:
            return []
        return fetch_security_groups(session, account_id, selected_vpc_id)

    sg_groups = with_all_accounts(fetch)
    sg_groups.sort(key=lambda g: g['rules'][0]['vpc_id'])

    account_ids = sorted({g['rules'][0]['account_id'] for g in sg_groups if g['rules']})
    vpc_ids = sorted({g['rules'][0]['vpc_id'] for g in sg_groups if g['rules']})

    return render(request, 'securitygroupdash/securitygroup_list.html', {
        'sg_groups': sg_groups,
        'account_ids': account_ids,
        'vpc_ids': vpc_ids,
        'selected_account_id': selected_account_id,
        'selected_vpc_id': selected_vpc_id,
    })