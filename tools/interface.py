import re
from datetime import datetime, date, timedelta
import json
from decimal import Decimal

from django.db.models import Sum, Q

from nt_s_common.decorator import cache_required
from .models import *


def show_notary_info_list():
    notary_names = Notaries.objects.filter(flag=1).values_list('name')
    return [name[0] for name in notary_names if name[0]]


def get_notary_region_rate():
    notary_names = Notaries.objects.filter(flag=1).values('region', 'granted_allowance')
    region_dict = {}
    for notary in notary_names:
        region = notary.get('region')
        region_dict.setdefault(region, 0)
        region_dict[region] += notary.get('granted_allowance')
    return region_dict


def get_notary_req(name):
    if not Notaries.objects.filter(name=name).count() and not Notaries.objects.filter(address=name).count():
        return 13000, ''
    nt = (Notaries.objects.filter(name=name) or Notaries.objects.filter(address=name)).values('address',
                                                                                              'github_accounts_dict',
                                                                                              'granted_allowance',
                                                                                              'region')[0]

    github_accounts_dict = nt.get('github_accounts_dict')
    git_list = [key for key, val in github_accounts_dict.items()]

    rats = RequestAllowanceRecord.objects.filter(assignee__in=git_list, flag=1).values('assignor', 'apply_address',
                                                                                       'created_at', 'region',
                                                                                       'request_datacap', 'status',
                                                                                       'allocated_datacap', 'msg_cid',
                                                                                       'comments_url', 'name', 'media')
    data_list = []
    for rat in rats:
        create_at = rat.get('created_at')
        data_list.append({
            'assignor': rat.get('assignor'),
            'request_datacap': rat.get('request_datacap'),
            'created_at': create_at.strftime('%Y-%m-%d %H:%M:%S') if create_at else create_at,
            'region': rat.get('region'),
            'apply_address': rat.get('apply_address'),
            'status': rat.get('status'),
            'allocated_datacap': rat.get('allocated_datacap'),
            'msg_cid': rat.get('msg_cid'),
            'url': get_req_url(rat.get('comments_url')),
            'height': get_height(msg_cid=rat.get('msg_cid')),
            'name': rat.get('name'),
            'issue_id': get_api_issue_id(rat.get('comments_url')),
            'media': rat.get('media'),
        })
        # print(data_list)
    return 0, data_list


def get_notary_info(name):
    if not Notaries.objects.filter(name=name).count() and not Notaries.objects.filter(address=name).count():
        return 13000, ''
    nt = (Notaries.objects.filter(name=name) or Notaries.objects.filter(address=name)).values('name', 'address',
                                                                                              'github_accounts_dict',
                                                                                              'granted_allowance',
                                                                                              'region',
                                                                                              'github_accounts_dict')[0]
    address = nt.get('address')
    github_accounts_dict = nt.get('github_accounts_dict')
    git_list = [key for key, val in github_accounts_dict.items()]
    refu = RequestAllowanceRecord.objects.filter(assignee__in=git_list, flag=1, status=0).aggregate(
        tt=Sum('request_datacap')).get('tt')
    allo = 0
    allo_data = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient').values(
        'msg_params')
    for data in allo_data:
        allo += Decimal(json.loads(data.get('msg_params')).get('Allowance'))
    tot = nt.get('granted_allowance')
    req_time = RequestAllowanceRecord.objects.filter(assignee__in=git_list, flag=1).count()
    data_dict = {}
    github_account = list(nt.get('github_accounts_dict').keys())[0]
    notary_info = {
        'address': address,
        'name': nt.get('name'),
        'refused': refu if refu else 0,
        'allow': allo if allo else 0,
        'total': tot,
        'req_time': req_time,
        'region': nt.get('region'),
        'github_name': github_account,
        'github_url': f'https://github.com/{github_account}'
    }
    data_dict['notary_info'] = notary_info
    # rats = RequestAllowanceRecord.objects.filter(assignee__in=git_list, flag=1, status=2).values('allocated_datacap',
    #                                                                                              'name')
    rats = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient').values(
        'msg_params')
    usage_dict = {}
    for rat in rats:
        ori_dict = json.loads(rat.get('msg_params'))
        key = ori_dict.get('Address')
        usage_dict.setdefault(key, 0)
        usage_dict[key] += Decimal(ori_dict.get('Allowance'))

    rate_dict = {}
    # 作用是解决少几次数据库的查询
    for key, val in usage_dict.items():
        if RequestAllowanceRecord.objects.filter(apply_address=key).count() or RequestAllowanceRecord.objects.filter(
                allocated_address=key).count():
            key = RequestAllowanceRecord.objects.filter(
                Q(apply_address=key) | Q(allocated_address=key)).first().name.strip('\r')
        rate_dict[key] = val
    rate_dict['unallow'] = tot - allo
    # rate_list = []
    # for k,v in rate_dict.items():
    #     rate_list.append({
    #
    #     })
    data_dict['rate_dict'] = rate_dict
    return 0, data_dict


def query_msg(msg_cid):
    code_re = {0: 'OK',
               1: 'SysErrSenderInvalid',
               2: 'SysErrSenderStateInvalid',
               3: 'SysErrInvalidMethod',
               4: 'SysErrReserved1',
               5: 'SysErrInvalidReceiver',
               6: 'SysErrInsufficientFunds',
               7: 'SysErrOutOfGas',
               8: 'SysErrForbidden',
               9: 'SysErrorlllegalActor',
               10: 'SysErrorlllegalArgument',
               11: 'SysErrReserved2',
               12: 'SysErrorReserved3',
               13: 'SysErrorReserved4',
               14: 'SysErrorReserved5',
               15: 'SysErrorReserved6',
               16: 'ErrIllegalArgument',
               17: 'ErrNotFound',
               18: 'ErrForbidden',
               19: 'ErrInsufficientFunds',
               20: 'ErrIllegalState',
               21: 'ErrSerialization',
               32: 'ErrTooManyProveCommits'}
    if not MessageDetails.objects.filter(msg_cid=msg_cid).count():
        return 13000, ''
    md = MessageDetails.objects.filter(msg_cid=msg_cid).values('msg_cid', 'height', 'height_time', 'msg_from', 'msg_to',
                                                               'msg_method_name', 'msg_value', 'msgrct_exit_code',
                                                               'msg_nonce', 'msg_gas_fee_cap', 'msg_gas_premium',
                                                               'msg_gas_limit', 'gascost_gas_used', 'base_fee','msg_return', 'msg_params')
    ret_data = md[0]
    ret_data['msg_params'] = json.loads(ret_data.get('msg_params'))
    ret_data['msg_return'] = json.loads(ret_data.get('msg_return'))
    ret_data['exit'] = code_re.get(ret_data.get('msgrct_exit_code'))
    return 0, ret_data


def get_provider_info_basic_info(provider_id):
    if not TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).count():
        return 13000, ''
    order_details_qset = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).values('deal_id',
                                                                                                         'height_time',
                                                                                                         'file_size',
                                                                                                         'client_address')
    total_size = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).aggregate(
        ts=Sum('file_size')).get('ts')
    order_details_list = []
    basic_info = {'provider_id': provider_id, 'num': order_details_qset.count(), 'total_size': total_size}
    query_data = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1,
                                                  order_date__isnull=False).order_by('height_time').values('order_date',
                                                                                                           'file_size')
    first_date = query_data[0].get('order_date')
    t_delta = (date.today() - first_date).days + 1
    order_stat = {}
    for delta in range(t_delta):
        order_stat.setdefault(first_date.strftime('%Y-%m-%d'), 0)
        first_date += timedelta(days=1)
    for data in query_data:
        order_stat[data.get('order_date').strftime('%Y-%m-%d')] += data.get('file_size')
    for order_details in order_details_qset:
        order_details_list.append(order_details)
    ret_data = {'basic_info': basic_info, 'order_stat': order_stat}
    return 0, ret_data


def get_provider_info_order_stat(provider_id):
    if not TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).count():
        return 13000, ''
    order_details_qset = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).values('deal_id',
                                                                                                         'height_time',
                                                                                                         'file_size',
                                                                                                         'client_address')
    total_size = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).aggregate(
        ts=Sum('file_size')).get('ts')
    order_details_list = []
    basic_info = {'provider_id': provider_id, 'num': order_details_qset.count(), 'total_size': total_size}
    query_data = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1,
                                                  order_date__isnull=False).order_by('height_time').values('order_date')
    first_date = query_data[0].get('order_date')
    t_delta = (date.today() - first_date).days + 1
    order_stat = {}
    for delta in range(t_delta):
        order_stat.setdefault(first_date.strftime('%Y-%m-%d'), 0)
        first_date += timedelta(days=1)
    for data in query_data:
        order_stat[data.get('order_date').strftime('%Y-%m-%d')] += 1
    for order_details in order_details_qset:
        order_details_list.append(order_details)
    # ret_data = {'basic_info': basic_info, 'order_stat': order_stat, 'order_details_list': order_details_list}
    time_list = []
    data_list = []
    for key, val in order_stat.items():
        time_list.append(key)
        data_list.append(val)
    return 0, time_list, data_list


def get_provider_info_order_details_list(provider_id):
    if not TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).count():
        return 13000, ''
    order_details_qset = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).values('deal_id',
                                                                                                         'height_time',
                                                                                                         'file_size',
                                                                                                         'client_address')
    total_size = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).aggregate(
        ts=Sum('file_size')).get('ts')
    order_details_list = []
    basic_info = {'provider_id': provider_id, 'num': order_details_qset.count(), 'total_size': total_size}
    query_data = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1,
                                                  order_date__isnull=False).order_by('height_time').values('order_date')
    first_date = query_data[0].get('order_date')
    t_delta = (date.today() - first_date).days + 1
    order_stat = {}
    for delta in range(t_delta):
        order_stat.setdefault(first_date.strftime('%Y-%m-%d'), 0)
        first_date += timedelta(days=1)
    for data in query_data:
        order_stat[data.get('order_date').strftime('%Y-%m-%d')] += 1
    for order_details in order_details_qset:
        # todo 处理时间
        order_details['height_time'] = order_details['height_time'].strftime('%Y-%m-%d') if order_details[
            'height_time'] else None
        order_details_list.append(order_details)
    ret_data = {'basic_info': basic_info, 'order_stat': order_stat, 'order_details_list': order_details_list}
    return 0, order_details_list


def get_provider_info_client_list(provider_id):
    if not TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).count():
        return 13000, ''
    order_details_qset = TransactionRecord.objects.filter(provider_id=provider_id, is_verified=1).values('file_size',
                                                                                                         'client_address')
    data_dict = {}
    ret_list = []
    for order_details in order_details_qset:
        address = order_details.get('client_address')
        data_dict.setdefault(address, {'total_size': 0, 'num': 0})
        data_dict[address]['total_size'] += order_details.get('file_size')
        data_dict[address]['num'] += 1
    for client_address, val in data_dict.items():
        # 写缓存
        data = get_notary_client_details(must_update_cache=False)
        if not data:
            data = get_notary_client_details(must_update_cache=True)
        notary_client_details = data.get(client_address)
        if not notary_client_details:
            notary_client_details = {'notaries': None, 'datacap': None}
        val['datacap'] = notary_client_details.get('datacap')
        val['notaries'] = ','.join(notary_client_details.get('notaries')) if notary_client_details.get(
            'notaries') else None
        val.update({'address': client_address})
        ret_list.append(val)
    return 0, ret_list


def get_name_list():
    notary_list = [i[0] for i in Notaries.objects.filter(flag=1).order_by('name').values_list('name').distinct()]
    client_list = list({i[0].strip() for i in RequestAllowanceRecord.objects.filter(flag=1).order_by('name').values_list('name').distinct() if i[0]})
    return {'notary_list': notary_list, 'client_list': client_list}


def get_new_seven_data():
    today_ = date.today()
    query_data = MessageDetails.objects.filter(msg_method_name='AddVerifiedClient',
                                               msg_date__gte=(today_ - timedelta(days=7))).order_by('msg_date').values(
        'msg_date', 'msg_params')
    data_dict = {}
    for i in range(7, 0, -1):
        data_dict.setdefault((today_ - timedelta(days=i)).strftime('%Y-%m-%d'), {'allowance': 0, 'count': 0})
    for data in query_data:
        j_data = json.loads(data.get('msg_params'))
        print(j_data.get('Allowance'), type(j_data.get('Allowance')))
        if data.get('msg_date').strftime('%Y-%m-%d') in data_dict:
            data_dict[data.get('msg_date').strftime('%Y-%m-%d')]['allowance'] += Decimal(j_data.get('Allowance'))
            data_dict[data.get('msg_date').strftime('%Y-%m-%d')]['count'] += 1
    data_list = []
    for key, val in data_dict.items():
        data_list.append({
            'time': key,
            'allowance': val.get('allowance'),
            'count': val.get('count'),
        })
    return 0, data_list


@cache_required(cache_key='notary_distribution_data', cache_key_type=1, expire=24 * 60 * 60)
def distribution_data(must_update_cache=False):
    nts = Notaries.objects.filter(flag=1).values('address',
                                                 'granted_allowance',
                                                 'github_accounts_dict')
    distribution_data = 0
    total_datacap = 0
    for nt in nts:
        address = nt.get('address')
        ghd = nt.get('github_accounts_dict')
        total_datacap += nt.get('granted_allowance') if nt.get('granted_allowance') else 0
        query_data = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient').values(
            'msg_params')
        for origin_data in query_data:
            distribution_data += Decimal(json.loads(origin_data.get('msg_params')).get('Allowance'))
        # query_data = RequestAllowanceRecord.objects.filter(assignee__in=ghd, status=2, flag=1).aggregate(
        #     tt=Sum('allocated_datacap')).get('tt') or 0
        # distribution_data += Decimal(query_data)
    total_datacap = Notaries.objects.all().aggregate(tt=Sum('granted_allowance')).get('tt')
    return 0, {'distribution_data': distribution_data, 'total_data': total_datacap,
               'distribution_data_rate': round(distribution_data / total_datacap, 2),
               'undistribution_data': 1 - round(distribution_data / total_datacap, 2)}


# def notary_distribution_data(notary_list):
#     print(notary_list)
#     notary_list = json.loads(notary_list) if notary_list else None
#     if notary_list:
#         if not Notaries.objects.filter(name__in=notary_list).count():
#             return 13000, ''
#     nts = Notaries.objects.filter(name__in=notary_list).values('address',
#                                                                'granted_allowance') if notary_list else Notaries.objects.filter(
#         flag=1).values('address', 'granted_allowance')
#     distribution_data = 0
#     total_datacap = 0
#     for nt in nts:
#         address = nt.get('address')
#         total_datacap += nt.get('granted_allowance') if nt.get('granted_allowance') else 0
#         query_data = MessageDetails.objects.filter(msg_from=address).values('msg_params')
#         # RequestAllowanceRecord.objects.filter()
#         for data in query_data:
#             distribution_data += Decimal(json.loads(data.get('msg_params')).get('Allowance'))
#
#     return 0, {'distribution_data': distribution_data, 'total_data': total_datacap,
#                'distribution_data_rate': round(distribution_data / total_datacap, 2),
#                'undistribution_data': 1 - round(distribution_data / total_datacap, 2)}


# def notary_distribution_data(notary_list):
#     notary_list = json.loads(notary_list) if notary_list else None
#     if notary_list:
#         if not Notaries.objects.filter(name__in=notary_list).count():
#             return 13000, ''
#     nts = Notaries.objects.filter(name__in=notary_list, flag=1).values('address',
#                                                                        'granted_allowance',
#                                                                        'github_accounts_dict') if notary_list else Notaries.objects.filter(
#         flag=1).values('address', 'granted_allowance', 'github_accounts_dict')
#     distribution_data = 0
#     total_datacap = 0
#     for nt in nts:
#         address = nt.get('address')
#         print(address)
#         ghd = nt.get('github_accounts_dict')
#         total_datacap += nt.get('granted_allowance') if nt.get('granted_allowance') else 0
#         # query_data = RequestAllowanceRecord.objects.filter(assignee__in=ghd, status=2, flag=1).aggregate(
#         #     tt=Sum('allocated_datacap')).get('tt') or 0
#         # distribution_data += Decimal(query_data)
#         query_data = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient').values(
#             'msg_params')
#         for origin_data in query_data:
#             distribution_data += Decimal(json.loads(origin_data.get('msg_params')).get('Allowance'))
#
#     return 0, {'distribution_data': distribution_data, 'total_data': total_datacap,
#                'distribution_data_rate': round(distribution_data / total_datacap, 2),
#                'undistribution_data': 1 - round(distribution_data / total_datacap, 2)}


@cache_required(cache_key='notary_distribution_data', cache_key_type=1, expire=24 * 60 * 60)
def notary_distribution_data(notary_list=None, must_update_cache=False):
    notary_list = json.loads(notary_list) if notary_list else None
    if notary_list:
        if not Notaries.objects.filter(name__in=notary_list).count():
            return 13000, ''
    nts = Notaries.objects.filter(name__in=notary_list, flag=1).values('address',
                                                                       'granted_allowance',
                                                                       'github_accounts_dict') if notary_list else Notaries.objects.filter(
        flag=1).values('address', 'granted_allowance', 'github_accounts_dict', 'region')
    distribution_data = 0
    distribution_data_24h = 0
    distribution_data_1d = 0
    total_datacap = 0
    region_list = []
    today_ = datetime.today()
    for nt in nts:
        region_list.append(nt.get('region'))
        address = nt.get('address')
        print(address)
        ghd = nt.get('github_accounts_dict')
        total_datacap += nt.get('granted_allowance') if nt.get('granted_allowance') else 0
        # query_data = RequestAllowanceRecord.objects.filter(assignee__in=ghd, status=2, flag=1).aggregate(
        #     tt=Sum('allocated_datacap')).get('tt') or 0
        # distribution_data += Decimal(query_data)
        query_data = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient').values(
            'msg_params')
        query_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        query_data_24h = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient',
                                                       height_time__range=(today_ - timedelta(days=1), today_)).values(
            'msg_params')
        query_data_1d = MessageDetails.objects.filter(msg_from=address, msg_method_name='AddVerifiedClient',
                                                      msg_date=query_date).values('msg_params')

        for origin_data in query_data:
            distribution_data += Decimal(json.loads(origin_data.get('msg_params')).get('Allowance'))
        for origin_data in query_data_24h:
            distribution_data_24h += Decimal(json.loads(origin_data.get('msg_params')).get('Allowance'))
        for origin_data in query_data_1d:
            distribution_data_1d += Decimal(json.loads(origin_data.get('msg_params')).get('Allowance'))

    return 0, {'distribution_data': distribution_data, 'total_data': total_datacap,
               'distribution_data_rate': round(distribution_data / total_datacap, 2),
               'undistribution_data': 1 - round(distribution_data / total_datacap, 2),
               'undistribution': total_datacap - distribution_data,
               'distribution_data_1d': distribution_data_1d,
               'nums': 23, 'region_num': len(set(region_list)), 'distribution_data_24h': distribution_data_24h}


def get_handle_efficiency(notary_list):
    notary_list = json.loads(notary_list) if notary_list else None
    query_data = RequestAllowanceRecord.objects.filter(status__in=(0, 2), flag=1).values('assignee', 'created_at',
                                                                                         'closed_at')
    data_dict = {}
    for data in query_data:
        assignee = data.get('assignee')
        data_dict.setdefault(assignee, [])
        data_dict[assignee].append(round((data.get('closed_at') - data.get('created_at')).total_seconds() / 3600, 2))
    data_list = []
    region_dict = {}
    for assignee, val in data_dict.items():
        if not assignee:
            continue
        if Notaries.objects.filter(github_accounts_dict__has_key=assignee).count():
            new_key = Notaries.objects.filter(github_accounts_dict__has_key=assignee).first().region
            if notary_list and new_key not in notary_list:
                continue
            region_dict.setdefault(new_key, [])
            region_dict[new_key].extend(val)
    for key, val in region_dict.items():
        data_list.append({
            'name': key,
            'max': max(val),
            'min': min(val),
            'avg': round(sum(val) / len(val), 2)
        })
    data_list.sort(key=lambda x: x.get('avg'))
    return 0, data_list


@cache_required(cache_key='get_handle_efficiency_borad_data', cache_key_type=1, expire=24 * 60 * 60)
def get_handle_efficiency_borad(must_update_cache=False):
    query_data = RequestAllowanceRecord.objects.filter(status__in=(2,), flag=1).values('assignee', 'created_at',
                                                                                       'closed_at')
    data_dict = {}
    for data in query_data:
        assignee = data.get('assignee')
        data_dict.setdefault(assignee, {'time': [], 'data': []})
        data_dict[assignee]['time'].append(
            round((data.get('closed_at') - data.get('created_at')).total_seconds() / 3600, 2))
    ret_dict = {}
    for assignee, val in data_dict.items():
        if Notaries.objects.filter(github_accounts_dict__has_key=assignee).count():
            nt = Notaries.objects.filter(github_accounts_dict__has_key=assignee).values('name', 'granted_allowance',
                                                                                        'region', 'address')[0]
            new_key = nt.get('name')
            ret_dict.setdefault(new_key, {})
            ret_dict[new_key]['avg'] = round(sum(val.get('time')) / len(val.get('time')), 2)
            ret_dict[new_key]['region'] = nt.get('region')
            ret_dict[new_key]['address'] = nt.get('address')
            ret_dict[new_key]['tot'] = nt.get('granted_allowance')
            ret_dict[new_key]['remain_datacap'] = nt.get('granted_allowance') - sum(val.get('data')) if nt.get(
                'granted_allowance') - sum(val.get('data')) > 0 else 0
            # print(RequestAllowanceRecord.objects.filter('assignee').aggregate(tt=Sum('request_datacap')).get('tt'))
            ret_dict[new_key]['request_datacap'] = RequestAllowanceRecord.objects.filter(assignee=assignee).aggregate(
                tt=Sum('request_datacap')).get('tt')
    nts = Notaries.objects.filter(flag=1).values('name', 'granted_allowance', 'region', 'address')
    nt_dict = {}
    for nt in nts:
        nt_dict.setdefault(nt.get('name'),
                           {'remain_datacap': nt.get('granted_allowance'), 'region': nt.get('region'),
                            # 'avg': 1000000000,
                            'avg': 0,
                            'allocated_datacap': 0, 'request_datacap': 0, 'address': nt.get('address'),
                            'tot': nt.get('granted_allowance'), })

    ret_list = []
    nt_dict.update(ret_dict)
    for key, val in nt_dict.items():
        msg_data = MessageDetails.objects.filter(msg_from=val.get('address'),
                                                 msg_method_name='AddVerifiedClient').values('msg_params')
        allocated_datacap = 0
        for data in msg_data:
            allocated_datacap += Decimal(json.loads(data.get('msg_params')).get('Allowance'))
        # print(val.get('remain_datacap')-allocated_datacap)
        ret_list.append({
            'notary': key,
            'avg': val.get('avg'),
            'region': val.get('region'),
            'allocated_datacap': allocated_datacap,
            'remain_datacap': val.get('remain_datacap') - allocated_datacap,
            'tot': val.get('tot'),
            'ratio': round(allocated_datacap / val.get('tot') * 100, 4) if val.get(
                'tot') else 0
        })
    # for item in ret_list:
    #     if item.get('avg') == 1000000000:
    #         item['avg'] = 0

    return ret_list


def get_handle_efficiency_borad_sort(sort_type, data):
    if_dict = {
        1: ('avg', False),
        2: ('avg', True),
        3: ('allocated_datacap', False),
        4: ('allocated_datacap', True),
        5: ('remain_datacap', False),
        6: ('remain_datacap', True),
        7: ('ratio', False),
        8: ('ratio', True),
    }
    if sort_type:
        if not sort_type.isdigit():
            return 13000, None
        sort_type = int(sort_type)
        data.sort(key=lambda x: x.get(if_dict.get(sort_type, ('ratio', True))[0]),
                  reverse=if_dict.get(sort_type, ('ratio', True))[1])
    return 0, data


def get_request_borad():
    query_data = RequestAllowanceRecord.objects.filter(flag=1, apply_address__isnull=False).values('apply_address',
                                                                                                   'allocated_datacap',
                                                                                                   'request_datacap',
                                                                                                   'assignor', 'name',
                                                                                                   'comments_url',
                                                                                                   'media')
    data_dict = {}
    data_list = []
    for data in query_data:
        apply_address = data.get('apply_address')
        data_dict.setdefault(apply_address, {'allocated_datacap': 0, 'request_datacap': 0, 'times': 0})
        data_dict[apply_address]['assignor'] = data.get('assignor')
        data_dict[apply_address]['name'] = data.get('name')
        data_dict[apply_address]['media'] = data.get('media')
        data_dict[apply_address]['comments_url'] = data.get('comments_url')
        data_dict[apply_address]['allocated_datacap'] += data.get('allocated_datacap') if data.get(
            'allocated_datacap') else 0
        data_dict[apply_address]['request_datacap'] += data.get('request_datacap') if data.get('request_datacap') else 0
        data_dict[apply_address]['times'] += 1
    for key, val in data_dict.items():
        data_list.append({
            'apply_address': key,
            'assignor': val.get('assignor'),
            'allocated_datacap': val.get('allocated_datacap'),
            'request_datacap': val.get('request_datacap'),
            'times': val.get('times'),
            'url': f'https://github.com/{val.get("assignor")}',
            'github_url': get_github_url(val.get('comments_url')),
            'issue_id': get_api_issue_id(val.get('comments_url')),
            'name': val.get('name'),
            'media': val.get('media')
        })
    return data_list


def get_request_borad_sort(data, sort_type):
    if_dict = {
        1: ('request_datacap', False),
        2: ('request_datacap', True),
        3: ('allocated_datacap', False),
        4: ('allocated_datacap', True),
        5: ('times', False),
        6: ('times', True),
    }
    if sort_type:
        if not sort_type.isdigit():
            return 13000, None
        sort_type = int(sort_type)
        if sort_type not in if_dict:
            sort_type = 4
    else:
        sort_type = 4
    data.sort(key=lambda x: x.get(if_dict.get(sort_type)[0]),
              reverse=if_dict.get(sort_type)[1])
    return 0, data


@cache_required(cache_key='get_provider_borad_data', cache_key_type=1, expire=24 * 60 * 60)
def get_provider_borad(must_update_cache=False):
    query_data = TransactionRecord.objects.filter(is_verified=1).order_by('provider_id').values('provider_id',
                                                                                                'file_size')
    data_dict = {}
    for data in query_data:
        provider = data.get('provider_id')
        data_dict.setdefault(provider, {'file_size': 0, 'times': 0})
        data_dict[provider]['file_size'] += data.get('file_size')
        data_dict[provider]['times'] += 1
    ret_list = []
    for key, val in data_dict.items():
        ret_list.append({
            'provider': key,
            'file_size': val.get('file_size'),
            'times': val.get('times'),
        })
    return ret_list


def get_provider_borad_sort(sort_type, data):
    if_dict = {
        1: ('times', False),
        2: ('times', True),
        3: ('file_size', False),
        4: ('file_size', True),
    }
    if sort_type:
        if not sort_type.isdigit():
            return 13000, None
        sort_type = int(sort_type)
        data.sort(key=lambda x: x.get(if_dict.get(sort_type, ('file_size', True))[0]),
                  reverse=if_dict.get(sort_type, ('file_size', True))[1])
    return 0, data


def get_user_info(address):
    if not TransactionRecord.objects.filter(client_address=address, is_verified=1).count():
        if RequestAllowanceRecord.objects.filter(apply_address=address).count():
            data_dict = {}
            data_dict['flow_data'] = []
            data_dict['assumption_data'] = []
            qta = (RequestAllowanceRecord.objects.filter(
                apply_address=address) or RequestAllowanceRecord.objects.filter(
                allocated_address=address)).values('assignor', 'request_datacap', 'allocated_datacap', 'media', 'name',
                                                   'comments_url')
            user_info = qta[0]
            basic_info = {
                'address': address,
                'apply_number': 0,
                'request_database': 0,
                'allocated_databse': 0,
                'github_account': user_info.get('assignor'),
                'user_url': f'https://github.com/{user_info.get("assignor")}',
                'name': user_info.get('name'),
                'media': user_info.get('media'),
                'github_url': get_github_url(user_info.get('comments_url')),
                'issue_id': get_api_issue_id(user_info.get('comments_url')),
            }
            for data in qta:
                basic_info['apply_number'] += 1
                print(data)
                basic_info['request_database'] += data.get('request_datacap') if data.get('request_datacap') else 0
                basic_info['allocated_databse'] += data.get('allocated_datacap') if data.get('allocated_datacap') else 0
                data_dict['basic_info'] = basic_info
            return 0, data_dict
        return 13000, ''
    data_dict = {}
    query_data = TransactionRecord.objects.filter(client_address=address, is_verified=1).order_by('order_date').values(
        'provider_id',
        'file_size',
        'order_date')
    flow_dict = {}
    assumption_dict = {}
    first_date = query_data[0].get('order_date')

    while first_date <= date.today():
        key = first_date.strftime('%Y-%m-%d')
        assumption_dict.setdefault(key, 0)
        first_date += timedelta(days=1)

    for data in query_data:
        provider = data.get('provider_id')
        date_key = data.get('order_date').strftime('%Y-%m-%d')
        flow_dict.setdefault(provider, 0)
        flow_dict[provider] += data.get('file_size')
        # assumption_dict[date_key] += 1
        assumption_dict[date_key] += data.get('file_size')
    flow_list = []
    for k, v in flow_dict.items():
        flow_list.append({
            'provider': k,
            'file_size': v,
        })
    assumption_list = []
    for k, v in assumption_dict.items():
        assumption_list.append({
            'date': k,
            'nums': v,
        })
    data_dict['flow_data'] = flow_list
    data_dict['assumption_data'] = assumption_list
    basic_info = {
        'address': address,
        'apply_number': None,
        'request_database': None,
        'allocated_databse': None,
        'github_account': None,
        'user_url': f'https://github.com',
    }
    if not RequestAllowanceRecord.objects.filter(
            apply_address=address).count() or not RequestAllowanceRecord.objects.filter(
        allocated_address=address).count():
        data_dict['basic_info'] = basic_info
        return 0, data_dict
    qta = (RequestAllowanceRecord.objects.filter(apply_address=address) or RequestAllowanceRecord.objects.filter(
        allocated_address=address)).values('assignor', 'request_datacap', 'allocated_datacap', 'name', 'media',
                                           'comments_url')
    basic_info = {
        'address': address,
        'apply_number': 0,
        'request_database': 0,
        'allocated_databse': 0,
        'github_account': qta[0].get('assignor'),
        'user_url': f'https://github.com/{qta[0].get("assignor")}',
        'name': qta[0].get('name'),
        'media': qta[0].get('media'),
        'github_url': get_github_url(qta[0].get('comments_url')),
        'issue_id': get_api_issue_id(qta[0].get('comments_url')),
    }
    for data in qta:
        basic_info['apply_number'] += 1
        basic_info['request_database'] += data.get('request_datacap') if data.get('request_datacap') else 0
        basic_info['allocated_databse'] += data.get('allocated_datacap') if data.get('allocated_datacap') else 0
    data_dict['basic_info'] = basic_info
    return 0, data_dict


def get_assumption_details(address):
    if not TransactionRecord.objects.filter(client_address=address, is_verified=1).count():
        return 13000, ''
    # if not TransactionRecord.objects.filter(client_address=address).count():
    #     return 13000, ''
    return 0, TransactionRecord.objects.filter(client_address=address, is_verified=1)


def request_record(address):
    if not RequestAllowanceRecord.objects.filter(apply_address=address,
                                                 flag=1).count() and not RequestAllowanceRecord.objects.filter(
        allocated_address=address, flag=1).count() and not RequestAllowanceRecord.objects.filter(
        assignor=address, flag=1).count():
        return 13000, ''
    return 0, RequestAllowanceRecord.objects.filter(apply_address=address,
                                                    flag=1) or RequestAllowanceRecord.objects.filter(
        allocated_address=address, flag=1) or RequestAllowanceRecord.objects.filter(
        assignor=address, flag=1)


def get_req_url(comments_url: str):
    try:
        num = re.search(r'/(\d+)/', comments_url).groups()[0]
        url = f'https://github.com/filecoin-project/filecoin-plus-client-onboarding/issues/{num}'
    except:
        url = None
    return url


def get_region_notary_disribution_rate(sort_type, region):
    """区域下公证人处理效率"""
    if not region:
        return 13000, None
    region_notary_dict = {}
    notaries = Notaries.objects.filter(region=region, flag=1).values('github_accounts_dict', 'granted_allowance',
                                                                     'name', 'allowance')
    for notary in notaries:
        region_notary_dict.setdefault(notary.get('name'),
                                      {'datacap': 0, 'allowance': 0, 'handle_time': 0, 'avaliable': 0, 'client_num': 0})
        region_notary_dict[notary.get('name')]['datacap'] = notary.get('granted_allowance')
        region_notary_dict[notary.get('name')]['allowance'] = notary.get('allowance')
        region_notary_dict[notary.get('name')]['available'] = notary.get('granted_allowance') - notary.get(
            'allowance') if (
                                    notary.get(
                                        'granted_allowance') - notary.get(
                                'allowance')) >= 0 else notary.get(
            'allowance')
        region_notary_dict[notary.get('name')]['handle_time'] = round(
            get_region_handle_effieciency(name=notary.get('name'))[0])
        region_notary_dict[notary.get('name')]['client_num'] = get_client_num(name=notary.get('name'))
    region_notary_list = []
    for key, val in region_notary_dict.items():
        region_notary_list.append(
            {'region': key, 'datacap': val.get('datacap'),
             'allowance': val.get('allowance'), 'handle_time': val.get('handle_time'),
             'client_num': val.get('client_num'), 'available': val.get('available')})
    if_dict = {
        1: ('client_num', False),
        2: ('client_num', True),
        3: ('datacap', False),
        4: ('datacap', True),
        5: ('allowance', False),
        6: ('allowance', True),
        7: ('available', False),
        8: ('available', True),
        9: ('handle_time', False),
        10: ('handle_time', True),
    }
    if sort_type:
        if not sort_type.isdigit():
            return 13000, None
        sort_type = int(sort_type)
        region_notary_list.sort(key=lambda x: x.get(if_dict.get(sort_type, ('handle_time', False))[0]),
                                reverse=if_dict.get(sort_type, ('handle_time', False))[1])
    return 0, region_notary_list


def get_client_num(name):
    notary_wallets = Notaries.objects.filter(name=name, flag=1).values('wallet__address')
    client_set = set()
    for notary_wallet in notary_wallets:
        address = notary_wallet.get('wallet__address')
        mds = MessageDetails.objects.filter(msg_method_name='AddVerifiedClient', msg_from=address).values('msg_params')
        for md in mds:
            msg_params = md.get('msg_params')
            client_set.add(json.loads(msg_params).get('Address'))
    return len(client_set)


def get_region_handle_effieciency(region=None, name=None):
    query_dict = get_not_none_dict(**{'region': region, 'name': name, 'flag': 1})
    notaries = Notaries.objects.filter(**query_dict).values('github_accounts_dict')
    data_list = []
    for notary in notaries:
        github_accounts_dict = notary.get('github_accounts_dict')
        for github in github_accounts_dict:
            reqs = RequestAllowanceRecord.objects.filter(assignee=github, status=2).values('created_at', 'closed_at')
            for req in reqs:
                data_list.append((req.get('closed_at') - req.get('created_at')).total_seconds() / (60 * 60))
    return sum(data_list) / len(data_list) if data_list else 0, data_list


def get_region_disribution_rate(sort_type):
    """区域处理效率"""
    region_dict = {}
    notaries = Notaries.objects.filter(flag=1).values('region', 'granted_allowance', 'name', 'allowance')
    for notary in notaries:
        region_dict.setdefault(notary.get('region'), {'num': 0, 'datacap': 0, 'allowance': 0, 'handle_time': 0})
        region_dict[notary.get('region')]['num'] += 1
        region_dict[notary.get('region')]['datacap'] += notary.get('granted_allowance')
        region_dict[notary.get('region')]['allowance'] += notary.get('allowance')
        region_dict[notary.get('region')]['handle_time'] = round(
            get_region_handle_effieciency(region=notary.get('region'))[0])
    region_list = []
    for key, val in region_dict.items():
        region_list.append(
            {'region': key, 'num': val.get('num'), 'datacap': val.get('datacap'),
             'allowance': val.get('allowance'), 'handle_time': val.get('handle_time')})
    if_dict = {
        1: ('num', False),
        2: ('num', True),
        3: ('datacap', False),
        4: ('datacap', True),
        5: ('allowance', False),
        6: ('allowance', True),
        7: ('handle_time', False),
        8: ('handle_time', True),
    }
    if sort_type:
        if not sort_type.isdigit():
            return 13000, None
        sort_type = int(sort_type)
        region_list.sort(key=lambda x: x.get(if_dict.get(sort_type, ('handle_time', False))[0]),
                         reverse=if_dict.get(sort_type, ('handle_time', False))[1])
    return 0, region_list


# tools
@cache_required(cache_key='notary_client_details', cache_key_type=1, expire=24 * 60 * 60)
def get_notary_client_details(must_update_cache=False):
    """refresh the details of the datacap that the notary has distributed"""
    data_dict = {}
    mds = MessageDetails.objects.filter(msg_method_name='AddVerifiedClient').values('msg_from', 'msg_params')
    for md in mds:
        notoray_address = md.get('msg_from')
        msg_params = json.loads(md.get('msg_params'))
        client_address = msg_params.get('Address')
        datacap = Decimal(msg_params.get('Allowance'))
        key = client_address + '-' + notoray_address
        data_dict.setdefault(key, 0)
        data_dict[key] += datacap
    ret_dict = {}
    for key, val in data_dict.items():
        client_address, notoray_address = key.split('-')
        if NotariesWallet.objects.filter(address=notoray_address).count():
            son_key = NotariesWallet.objects.filter(address=notoray_address).first().notary.name
        else:
            son_key = notoray_address
        ret_dict.setdefault(client_address, {'notaries': [], 'datacap': 0})
        ret_dict[client_address]['notaries'].append(son_key)
        ret_dict[client_address]['datacap'] += val
    return ret_dict


def add_new_github(account, account_dict):
    if account and account not in account_dict:
        account_dict.update({account: account})
    return account_dict


def add_dict_data(id, account):
    nt = Notaries.objects.filter(id=id).first()
    nt.github_accounts_dict = add_new_github(account, nt.github_accounts_dict)
    nt.save()


def handle_page(pp: str, default: int):
    if pp and pp.strip():
        return int(pp)
    else:
        return default


def get_height(msg_cid):
    if MessageDetails.objects.filter(msg_cid=msg_cid).count():
        return MessageDetails.objects.filter(msg_cid=msg_cid).first().height
    else:
        return None


def get_github_url(comments_url: str):
    if comments_url:
        b = re.search(r'\d+', comments_url).group()
        return f'https://github.com/filecoin-project/filecoin-plus-client-onboarding/issues/{b}'


def get_api_issue(comments_url: str):
    if comments_url:
        b = re.search(r'\d+', comments_url).group()
        return f'https://api.github.com/repos/filecoin-project/filecoin-plus-client-onboarding/issues/{b}'


def get_api_issue_id(comments_url: str):
    if comments_url:
        b = re.search(r'\d+', comments_url).group()
        return b


def get_notary_by_github_account(assignee: str):
    if Notaries.objects.filter(github_accounts_dict__has_key=assignee).count():
        return Notaries.objects.filter(github_accounts_dict__has_key=assignee).first().name


def get_not_none_dict(**dic: dict):
    new_dict = {}
    for key, val in dic.items():
        if val or isinstance(val, int):
            new_dict.setdefault(key, val)
    return new_dict
