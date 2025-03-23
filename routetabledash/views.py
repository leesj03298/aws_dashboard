import boto3
from django.shortcuts import render

def route_table_list(request):
    ec2 = boto3.client('ec2', region_name='ap-northeast-2')
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']

    # ✅ GET 파라미터에서 선택된 VPC ID 가져오기
    selected_vpc_id = request.GET.get('vpc_id')

    route_tables = []
    vpc_ids_set = set()

    response = ec2.describe_route_tables()

    for rtb in response['RouteTables']:
        tags = {t['Key']: t['Value'] for t in rtb.get('Tags', [])}
        vpc_id = rtb.get('VpcId', '')
        vpc_ids_set.add(vpc_id)  # ✅ VPC ID 목록 저장

        # Associations
        associations = []
        for assoc in rtb.get('Associations', []):
            associations.append({
                'subnet': assoc.get('SubnetId', ''),
                'default': assoc.get('Main', False)
            })

        # Routes
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
            routes.append({'cidr': cidr, 'target': target})

        # ✅ local 우선 정렬
        routes.sort(key=lambda r: 0 if r['target'] == 'local' else 1)
        route_tables.sort(key=lambda x: x['vpc_id'])

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

    # ✅ 선택된 VPC ID로 필터링
    if selected_vpc_id:
        route_tables = [r for r in route_tables if r['vpc_id'] == selected_vpc_id]

    # ✅ VPC ID 목록 추출 (select box용)
    vpc_ids = sorted(vpc_ids_set)

    return render(request, 'routetabledash/routetable_list.html', {
        'route_tables': route_tables,
        'vpc_ids': vpc_ids,
        'selected_vpc_id': selected_vpc_id,
    })
