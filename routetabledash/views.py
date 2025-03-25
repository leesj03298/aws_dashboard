from django.shortcuts import render
from common.aws_multi import with_all_accounts

def fetch_route_tables(session, account_id, account_name):
    ec2 = session.client('ec2', region_name='ap-northeast-2')
    response = ec2.describe_route_tables()

    route_tables = []

    for rtb in response['RouteTables']:
        tags = {t['Key']: t['Value'] for t in rtb.get('Tags', [])}
        vpc_id = rtb.get('VpcId', '')

        associations = []
        for assoc in rtb.get('Associations', []):
            associations.append({
                'subnet': assoc.get('SubnetId', ''),
                'default': assoc.get('Main', False)
            })

        routes = []
        for route in rtb.get('Routes', []):
            cidr = route.get('DestinationCidrBlock') or route.get('DestinationIpv6CidrBlock', '')
            target = (
                route.get('GatewayId') or
                route.get('NatGatewayId') or
                route.get('TransitGatewayId') or
                route.get('InstanceId') or
                'local'
            )
            routes.append({
                'cidr': cidr,
                'target': target
            })

        # ✅ local 우선 정렬
        routes.sort(key=lambda r: 0 if r['target'] == 'local' else 1)

        # 병합용 zip
        max_len = max(len(associations), len(routes))
        merged = zip(
            associations + [{'subnet': '', 'default': False}] * (max_len - len(associations)),
            routes + [{}] * (max_len - len(routes))
        )

        route_tables.append({
            'account_id': account_id,
            'name': tags.get('Name', ''),
            'id': rtb['RouteTableId'],
            'vpc_id': vpc_id,
            'tags': tags,
            'rows': list(merged),
            'rowspan': max_len
        })

    return route_tables


def route_table_list(request):
    route_tables = with_all_accounts(fetch_route_tables)

    # ✅ VPC 기준 정렬
    route_tables.sort(key=lambda x: x['vpc_id'])

    return render(request, 'routetabledash/routetable_list.html', {
        'route_tables': route_tables
    })
