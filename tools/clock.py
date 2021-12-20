import json
import os
import re
from decimal import Decimal

import requests
from datetime import datetime, timedelta, date
from django.db import transaction

from nt_s_common.decorator import cache_required
from nt_s_common.third.xm_sdk import XmBase
from tools.interface import distribution_data, get_handle_efficiency_borad, get_provider_borad, \
    notary_distribution_data, get_api_issue, get_notary_client_details
from tools.models import MessageDetails, TransactionRecord, RequestAllowanceRecord, NotariesWallet, Notaries

headers = {'AppId': 'h5b9557f39e2f84d', 'AppVersion': '1.0.0'}
d_types = ('AddVerifiedClient', 'PublishStorageDeals')


def request_data(url, body, headers, repeat_time=10):
    initial_time = 1
    while initial_time < repeat_time:
        print(f'尝试第{initial_time}次')
        print(f'body---{body}')
        try:
            req = requests.post(url, headers=headers, data=body, timeout=30)
        except Exception as e:
            print(e)
            initial_time += 1
            continue
        if req.status_code == 200:
            return req.json().get('data')
        initial_time += 1


def request_data_get(url, params, headers, repeat_time=10):
    initial_time = 1
    while initial_time < repeat_time:
        print(f'尝试第{initial_time}次')
        try:
            req = requests.get(url, headers=headers, params=params, timeout=10)
        except Exception as e:
            print(e)
            initial_time += 1
            continue
        if req.status_code == 200:
            return req.json()
        initial_time += 1


def get_height(target=None):
    """ get height """
    if not target:
        target = datetime.today()
    sub = target.timestamp() - datetime(2020, 8, 25, 6, 0, 0).timestamp()
    return int(sub / 30)


def get_height_list(target=None):
    if not target:
        target = date.today()
    end_time = datetime.combine(target, datetime.min.time())
    end_height = get_height(end_time)
    print(end_height, end_time)
    return [end_height - i for i in range(0, 2881)]


def get_deal_data():
    """deal id 订单"""
    initial_page = 1
    flag = True
    page_log = set()
    page_size = 50
    while flag:
        page_watch = 0
        data = {'page_index': str(initial_page), 'page_size': str(page_size), 'is_verified': 1}
        res = XmBase().get_deal_list(data=data).get('data')
        print(f'page----{initial_page}')
        data = res.get('objects')
        if not data:
            print(data)
            print('exit')
            break
        for index, info in enumerate(data, start=1):
            deal_id = info.get('deal_id')
            create_data = {
                'height_time': info.get('height_time'),
                'deal_id': deal_id,
                'file_size': info.get('piece_size'),
                'is_verified': info.get('is_verified'),
                'client_address': info.get('client'),
                'provider_id': info.get('provider'),
                'height': info.get('height'),
                'order_date': datetime.strptime(info.get('height_time'), '%Y-%m-%d %H:%M:%S').date() if info.get(
                    'height_time') else info.get('height_time')
            }
            if TransactionRecord.objects.filter(deal_id=deal_id).count():
                print('old data')
                page_watch += 1
                if page_watch == page_size:
                    page_log.add(initial_page)
                if len(page_log) == 20:
                    flag = False
                    break
                continue
            print('new data')
            TransactionRecord.objects.create(**create_data)
        initial_page += 1


def get_ts_date():
    for idd in range(1420001, 3029081):
        print(idd)
        if not TransactionRecord.objects.filter(id=idd, height_time__isnull=False, order_date__isnull=True).count():
            continue
        tr = TransactionRecord.objects.filter(id=idd).first()
        if tr.height_time:
            tr.order_date = tr.height_time.date()
            tr.save()


def get_msg_cid(target=None):
    """get msg list"""
    msg_cid_list = []
    for d_type in d_types:
        print(d_type)
        height_list = get_height_list(target)
        for height in height_list:
            initial_page = 1
            flag = True
            while flag:
                data = {'msg_method': d_type, 'page_size': 50, 'page_index': str(initial_page), 'height': height}
                req = XmBase().get_message_list(data=data).get('data')
                objs = req.get('objects')
                if not objs:
                    print(1)
                    break
                # if the item length in one page is smaller than 50, we will stop here
                obj_length = len(objs)
                if obj_length < 50:
                    flag = False
                for index, data in enumerate(objs):
                    msg_cid = data.get("msg_cid")
                    height = data.get("height")
                    if MessageDetails.objects.filter(msg_cid=msg_cid).count():
                        print('old')
                        continue
                    create_data = get_msg_detail(msg_cid, height)
                    print(f'new---{msg_cid}')
                    MessageDetails.objects.create(**create_data)
                initial_page += 1
    # get the amount of datacap that the notary has distributed
    cal_allowance()
    # refresh the details of the datacap that the notary has distributed
    get_notary_client_details(must_update_cache=True)


def get_msg_detail(msg_cid, height):
    data = {'msg_cid': msg_cid, 'height': height}
    req = XmBase().get_message_info(data).get('data')
    od = {
        'msg_cid': req.get('msg_cid'),
        'height': req.get('height'),
        'height_time': req.get('height_time'),

        'msg_from': req.get('msg_from'),
        'msg_to': req.get('msg_to'),
        'msg_method': req.get('msg_method'),
        'msg_method_name': req.get('msg_method_name'),
        'msg_value': req.get('msg_value'),
        'msgrct_exit_code': req.get('msgrct_exit_code'),

        'gascost_miner_penalty': req.get('gascost_miner_penalty'),
        'gascost_refund': req.get('gascost_refund'),
        'gascost_base_fee_burn': req.get('gascost_base_fee_burn'),
        'gascost_total_cost': req.get('gascost_total_cost'),
        'gascost_miner_tip': req.get('gascost_miner_tip'),
        'gascost_over_estimation_burn': req.get('gascost_over_estimation_burn'),

        'msg_nonce': req.get('msg_nonce'),
        'msg_gas_fee_cap': req.get('msg_gas_fee_cap'),
        'msg_gas_premium': req.get('msg_gas_premium'),
        'msg_gas_limit': req.get('msg_gas_limit'),
        'gascost_gas_used': req.get('gascost_gas_used'),
        'base_fee': req.get('base_fee'),
        'msg_return': req.get('msg_return'),
        'msg_params': req.get('msg_params'),
        'msg_date': datetime.strptime(req.get("height_time"), '%Y-%m-%d %H:%M:%S').date()
    }
    if req.get('msg_method_name') == 'PublishStorageDeals':
        for dd in json.loads(req.get('msg_params')).get("Deals"):
            if dd.get('Proposal').get('VerifiedDeal'):
                od['status'] = 1
            else:
                od['status'] = 0
    return od


# datacap request records


def initial_req():
    """get datacap requests"""
    state_choices = ('closed', 'open')
    url = 'https://api.github.com/repos/filecoin-project/filecoin-plus-client-onboarding/issues'
    body_list = []
    a = []
    b = []
    data_list = []
    for choice_ in state_choices:
        ff = True
        initial_page = 1
        while ff:
            github_token = os.getenv('github_token')
            headers = {"Authorization": github_token}
            # req = requests.get(url, headers=headers, proxies=proxies,params={'state': choice_, 'per_page': '100', 'page': str(initial_page)}).json()
            req = request_data_get(url, headers=headers,
                                   params={'state': choice_, 'per_page': '100', 'page': str(initial_page)})
            print(f'initial_req--{req}')
            if not req:
                break
            for data in req:
                assignor = data.get('user').get('login')
                issue_state = data.get('state')
                labels = data.get('labels')
                created_at = data.get('created_at')
                closed_at = data.get('closed_at')
                updated_at = data.get('updated_at')
                comments_url = data.get('comments_url')
                issue_body = data.get('body')
                assignee = data.get("assignee").get('login') if data.get("assignee") else None
                title = data.get("title")
                if re.search(r'test', title, re.I):
                    continue
                msg_cid = None
                allocated_address = None
                allocated_datacap = None
                flag = True

                # print(assignor, issue_state, comments_url, assignee)
                # ((0, 'closed but not distributed'), (1, 'handling'), (2, 'distributed'))
                status = 0 if state_choices == 'closed' else 1

                print(issue_body)
                print(data.get('url'))
                if not issue_body:
                    continue
                if not (re.search(r'name: (.*?)\n', issue_body, re.M | re.I) or re.search(r'name:(.*?)\n', issue_body,
                                                                                          re.M | re.I)):
                    continue
                if (re.search(r'name: (.*?)\n', issue_body, re.M | re.I) or re.search(r'name:(.*?)\n', issue_body,
                                                                                      re.M | re.I)).groups()[0] == '\r':
                    continue
                name = (re.search(r'name: (.*?)\n', issue_body, re.M | re.I) or re.search(r'name:(.*?)\n', issue_body,
                                                                                          re.M | re.I)).groups()[0]
                media = \
                    (re.search(r'Website(.*?): (.*?)\n', issue_body, re.M | re.I) or re.search(r'Website(.*?):(.*?)\n',
                                                                                               issue_body,
                                                                                               re.M | re.I)).groups()[1]
                apply_address = re.search(r'(f1\w{5,}|f2\w{5,}|f3\w{5,})', issue_body, re.M | re.I).groups(
                    [0]) if re.search(r'(f1\w{5,}|f2\w{5,}|f3\w{5,})', issue_body, re.M | re.I) else None
                region = re.search(r'Region: (.*?)\n', issue_body, re.M | re.I).groups()[0] if re.search(
                    r'Region: (.*?)\n',
                    issue_body,
                    re.M | re.I) else None
                request_datacap = (re.search(r'(DataCap.*?): (\d+.*)', issue_body) or re.search(r'(DataCap.*?):(\d+.*)',
                                                                                                issue_body) or re.search(
                    r'(DataCap.*?):(.{3,})', issue_body)).groups()[1]
                print(f'rrrrrrrrrrrrrrrrrrrr-{request_datacap}---{type(request_datacap)}')
                for label in labels:
                    print(issue_state, comments_url, initial_page)
                    if 'Granted' in label.get('name'):
                        a.append(comments_url)
                        # ret1 = requests.get(url=comments_url, proxies=proxies, headers=headers).json()
                        ret1 = requests.get(url=comments_url, headers=headers).json()
                        for ret in ret1:
                            body_data = ret.get('body')
                            if 'Datacap Allocated' in body_data:
                                b.append(comments_url)
                                msg_cid = list(set(re.findall(r'(bafy\w*)', body_data, re.M)))
                                allocated_address = (re.search(r'> (f\w{7,})', body_data) or re.search(
                                    r'\[(f1\w{5,}|f2\w{5,}|f3\w{5,})\]', body_data)).groups()[0]
                                print(body_data)
                                allocated_datacap = \
                                    (re.search(r'> (\d+.*)', body_data) or re.search(r'>(\d+.*)',
                                                                                     body_data) or re.search(
                                        r'> (\d+.*)', issue_body) or re.search(r'>(\d+.*)', body_data)).groups()[0] if (
                                            re.search(r'> (\d+.*)', body_data) or re.search(r'>(\d+.*)',
                                                                                            body_data) or re.search(
                                        r'> (\d+.*)', issue_body) or re.search(r'>(\d+.*)', body_data)) else 0
                                body_list.append(ret.get('body'))
                                if flag:
                                    print(request_datacap)
                                    if request_datacap and request_datacap.strip() != 'None':
                                        request_datacap = request_datacap.strip()
                                        if not re.match(r'^\d', request_datacap):
                                            request_datacap = re.search(r'(\d.*\w+)', request_datacap).groups()[
                                                0].strip()
                                        origin_data = (re.search(r'(.*?)(T|G|P|t|g|p|K|k|M|m)', request_datacap))
                                        num = origin_data.groups()[0].strip()
                                        unit = origin_data.groups()[1].strip()
                                        print('>>>>>>>>>>>>>>>', num, unit, unit.startswith('T'), unit.startswith('t'))
                                        if unit.startswith('P') or unit.startswith('p'):
                                            request_datacap = Decimal(num) * (1024 ** 5)
                                        elif unit.startswith('T') or unit.startswith('t'):
                                            request_datacap = Decimal(num) * (1024 ** 4)
                                        elif unit.startswith('G') or unit.startswith('g'):
                                            request_datacap = Decimal(num) * (1024 ** 3)
                                        elif unit.startswith('M') or unit.startswith('m'):
                                            request_datacap = Decimal(num) * (1024 ** 2)
                                        elif unit.startswith('K') or unit.startswith('k'):
                                            request_datacap = Decimal(num) * (1024 ** 1)
                                    else:
                                        request_datacap = None
                                    print(allocated_datacap)
                                    if allocated_datacap and allocated_datacap.strip() != 'None':
                                        allocated_datacap = allocated_datacap.strip()
                                        if not re.match(r'^\d', allocated_datacap):
                                            allocated_datacap = re.search(r'(\d.*\w+)', allocated_datacap).groups()[
                                                0].strip()
                                        origin_data = re.search(r'(.*?)(T|G|P|t|g|p|K|k|M|m)', allocated_datacap)
                                        num = origin_data.groups()[0].strip()
                                        unit = origin_data.groups()[1].strip()
                                        print('>>>>>>>>>>>>>>>', num, unit, unit.startswith('T'), unit.startswith('t'))
                                        if unit.startswith('P') or unit.startswith('p'):
                                            allocated_datacap = Decimal(num) * (1024 ** 5)
                                        elif unit.startswith('T') or unit.startswith('t'):
                                            allocated_datacap = Decimal(num) * (1024 ** 4)
                                        elif unit.startswith('G') or unit.startswith('g'):
                                            allocated_datacap = Decimal(num) * (1024 ** 3)
                                        elif unit.startswith('M') or unit.startswith('m'):
                                            allocated_datacap = Decimal(num) * (1024 ** 2)
                                        elif unit.startswith('K') or unit.startswith('k'):
                                            allocated_datacap = Decimal(num) * (1024 ** 1)
                                    else:
                                        allocated_datacap = None
                                    status = 2
                                    create_dict = {
                                        'name': name,
                                        'media': media,
                                        'region': region,
                                        'request_datacap': request_datacap if request_datacap else 0,
                                        'assignor': assignor,
                                        'created_at': datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ'),
                                        'closed_at': datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ'),
                                        'updated_at': datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ'),
                                        'comments_url': comments_url,
                                        'assignee': assignee,
                                        'status': status,
                                        'msg_cid': msg_cid[0] if msg_cid else msg_cid,
                                        'apply_address': apply_address[0] if apply_address else apply_address,
                                        'allocated_address': allocated_address,
                                        'allocated_datacap': allocated_datacap if allocated_datacap else 0,
                                        'distribute_date': datetime.strptime(closed_at,
                                                                             '%Y-%m-%dT%H:%M:%SZ').date() if status == 2 else None
                                    }
                                    flag = False
                                    if not RequestAllowanceRecord.objects.filter(
                                            comments_url=create_dict.get('comments_url')).count():
                                        RequestAllowanceRecord.objects.create(**create_dict)
                                    elif RequestAllowanceRecord.objects.filter(
                                            comments_url=create_dict.get('comments_url'),
                                            closed_at__isnull=True).count():
                                        RequestAllowanceRecord.objects.filter(
                                            comments_url=create_dict.get('comments_url'),
                                            closed_at__isnull=True).update(**create_dict)
                                    else:
                                        ff = False if choice_ == 'open' else True
                                        break
                if flag:
                    print(request_datacap, type(request_datacap))
                    if request_datacap and request_datacap.strip() != 'None':
                        request_datacap = request_datacap.strip()
                        if not re.match(r'^\d', request_datacap):
                            request_datacap = re.search(r'(\d.*\w+)', request_datacap).groups()[0].strip() if re.search(
                                r'(\d.*\w+)', request_datacap) else None
                        if request_datacap:
                            origin_data = re.search(r'(.*?)(T|G|P|t|g|p|K|k|M|m)', request_datacap)
                            if origin_data:
                                num = origin_data.groups()[0].strip()
                                unit = origin_data.groups()[1].strip()
                                print('>>>>>>>>>>>>>>>', num, unit, unit.startswith('T'), unit.startswith('t'))
                                if unit.startswith('P') or unit.startswith('p'):
                                    request_datacap = Decimal(num) * (1024 ** 5)
                                elif unit.startswith('T') or unit.startswith('t'):
                                    request_datacap = Decimal(num) * (1024 ** 4)
                                elif unit.startswith('G') or unit.startswith('g'):
                                    request_datacap = Decimal(num) * (1024 ** 3)
                                elif unit.startswith('M') or unit.startswith('m'):
                                    request_datacap = Decimal(num) * (1024 ** 2)
                                elif unit.startswith('K') or unit.startswith('k'):
                                    request_datacap = Decimal(num) * (1024 ** 1)
                            else:
                                request_datacap = 0
                        else:
                            request_datacap = 0
                    else:
                        request_datacap = None
                    print(allocated_datacap)
                    if allocated_datacap and allocated_datacap.strip() != 'None':
                        allocated_datacap = allocated_datacap.strip()
                        if not re.match(r'^\d', allocated_datacap):
                            allocated_datacap = re.search(r'(\d.*\w+)', allocated_datacap).groups()[0].strip()
                        origin_data = re.search(r'(.*?)(T|G|P|t|g|p|K|k|M|m)', allocated_datacap)
                        num = origin_data.groups()[0].strip()
                        unit = origin_data.groups()[1].strip()
                        print('>>>>>>>>>>>>>>>', num, unit, unit.startswith('T'), unit.startswith('t'))
                        if unit.startswith('P') or unit.startswith('p'):
                            allocated_datacap = Decimal(num) * (1024 ** 5)
                        elif unit.startswith('T') or unit.startswith('t'):
                            allocated_datacap = Decimal(num) * (1024 ** 4)
                        elif unit.startswith('G') or unit.startswith('g'):
                            allocated_datacap = Decimal(num) * (1024 ** 3)
                        elif unit.startswith('M') or unit.startswith('m'):
                            allocated_datacap = Decimal(num) * (1024 ** 2)
                        elif unit.startswith('K') or unit.startswith('k'):
                            allocated_datacap = Decimal(num) * (1024 ** 1)
                    else:
                        allocated_datacap = None
                    create_dict = {
                        'name': name,
                        'media': media,
                        'region': region,
                        'request_datacap': request_datacap if request_datacap else 0,
                        'assignor': assignor,
                        'created_at': datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ'),
                        'closed_at': datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ') if closed_at else None,
                        'updated_at': datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ'),
                        'comments_url': comments_url,
                        'assignee': assignee,
                        'status': status,
                        'msg_cid': msg_cid[0] if msg_cid else msg_cid,
                        'apply_address': apply_address[0] if apply_address else apply_address,
                        'allocated_address': allocated_address,
                        'allocated_datacap': allocated_datacap if allocated_datacap else 0,
                        'distribute_date': datetime.strptime(closed_at,
                                                             '%Y-%m-%dT%H:%M:%SZ').date() if status == 2 else None
                    }
                    flag = False
                    if not RequestAllowanceRecord.objects.filter(comments_url=create_dict.get('comments_url')).count():
                        RequestAllowanceRecord.objects.create(**create_dict)
                    elif RequestAllowanceRecord.objects.filter(comments_url=create_dict.get('comments_url'),
                                                               closed_at__isnull=True).count():
                        RequestAllowanceRecord.objects.filter(comments_url=create_dict.get('comments_url'),
                                                              closed_at__isnull=True).update(**create_dict)
                    else:
                        ff = False if choice_ == 'open' else True
                        break
            initial_page += 1


def refresh_data_now():
    distribution_data(must_update_cache=True)
    notary_distribution_data(must_update_cache=True)
    get_handle_efficiency_borad(must_update_cache=True)
    get_provider_borad(must_update_cache=True)


def get_unkown_address():
    reqs = RequestAllowanceRecord.objects.filter(apply_address__isnull=True)
    for req in reqs:
        api_issue_url = get_api_issue(req.comments_url)
        if not api_issue_url:
            continue
        headers = {"Authorization": 'token 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'}
        data = request_data_get(url=api_issue_url, headers=headers, params=None)
        body = data.get('body')
        apply_address = re.search(r'Addresses to be Notarized:(.*)', body)
        req.apply_address = apply_address.groups()[0].strip()
        req.save()


def get_check_closed_issue():
    reqs = RequestAllowanceRecord.objects.filter(status=1, create_time__lt=datetime.today())
    print(reqs)
    for req in reqs:
        print(req)
        comments_url = req.comments_url
        api_issue_url = get_api_issue(comments_url)
        if not api_issue_url:
            continue
        headers = {"Authorization": 'token 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'}
        data = request_data_get(url=api_issue_url, headers=headers, params=None)
        state = data.get('state')
        labels = data.get('labels')
        closed_at = data.get('closed_at')
        if state == 'closed':
            for label in labels:
                if 'Granted' in label.get('name'):
                    # data = request_data_get(url=comments_url, headers=headers, params=None)
                    req.status = 2
                    req.closed_at = datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ')
                    req.save()
                else:
                    req.status = 0
                    req.closed_at = datetime.strptime(closed_at, '%Y-%m-%dT%H:%M:%SZ')
                    req.save()


def cal_allowance():
    """get the amount of datacap that the notary has distributed"""
    nts = Notaries.objects.filter(flag=1)
    for nt in nts:
        address_data = nt.wallet.values('address')
        distribution_data = 0
        for address_qs in address_data:
            address = address_qs.get('address')
            mds = MessageDetails.objects.filter(msg_method_name='AddVerifiedClient', msg_from=address).values(
                'msg_params')
            for md in mds:
                msg_params = md.get('msg_params')
                distribution_data += Decimal(json.loads(msg_params).get('Allowance'))
        nt.allowance = distribution_data
        nt.save()


def refresh_now():
    """refresh the redis data"""
    distribution_data(must_update_cache=True)
    notary_distribution_data(notary_list=None, must_update_cache=True)
    get_handle_efficiency_borad(must_update_cache=True)
    get_provider_borad(must_update_cache=True)
    get_notary_client_details(must_update_cache=True)
