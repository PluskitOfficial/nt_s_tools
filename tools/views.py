import json
import datetime
import decimal

from nt_s_common.cache import Cache
from nt_s_common.decorator import common_ajax_response, lang_translate
from nt_s_common.page import Page
from nt_s_common.utils import format_return, ERROR_DICT
from tools import interface, clock
from tools.clock import initial_req, get_msg_cid, get_deal_data, get_unkown_address, \
    get_check_closed_issue, refresh_data_now
from nt_s_tools.consts import ERROR_DICT
from tools.interface import get_height, get_github_url, get_api_issue_id, get_notary_by_github_account


@common_ajax_response
@lang_translate
def show_notary_info_list(request):
    """display notary list"""
    data = interface.show_notary_info_list()
    return format_return(0, data=data)


@common_ajax_response
@lang_translate
def notary_region_rate(request):
    """显示公证人按照大区比例"""
    data_rate = interface.get_notary_region_rate()
    return format_return(0, data=data_rate)


@common_ajax_response
@lang_translate
def notary_info(request):
    """get notary details"""
    name = request.POST.get('name')
    if not name:
        return format_return(13000)
    msg_code, msg_data = interface.get_notary_info(name=name.strip(''))
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def notary_req(request):
    """"show datacap request record """
    page_index = request.POST.get('page_index', '1')
    page_size = request.POST.get('page_size', '5')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    name = request.POST.get('name').strip('')
    msg_code, msg_data = interface.get_notary_req(name=name)
    total = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'data': msg_data, 'total': total})


@common_ajax_response
@lang_translate
def query_msg(request):
    """get msg details"""
    msg_cid = request.POST.get('msg_cid')
    msg_code, msg_data = interface.query_msg(msg_cid=msg_cid)
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def provider_info_basic_info(request):
    """basic info of provider info"""
    provider_id = request.POST.get('provider_id')
    msg_code, msg_data = interface.get_provider_info_basic_info(provider_id=provider_id)
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def provider_info_order_stat(request):
    """order stat of provider info"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    provider_id = request.POST.get('provider_id')
    msg_code, msg_data1, msg_data2 = interface.get_provider_info_order_stat(provider_id=provider_id)
    msg_data1 = msg_data1[(page_size * (page_index - 1)):page_size * page_index]
    msg_data2 = msg_data2[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'time': msg_data1, 'data': msg_data2})


@common_ajax_response
@lang_translate
def provider_info_order_details_list(request):
    """order details list of provider info"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    provider_id = request.POST.get('provider_id')
    msg_code, msg_data = interface.get_provider_info_order_details_list(provider_id=provider_id)
    total = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'data': msg_data, 'total': total})


@common_ajax_response
@lang_translate
def provider_info_client_list(request):
    """client list of provider info"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    provider_id = request.POST.get('provider_id')
    msg_code, msg_data = interface.get_provider_info_client_list(provider_id=provider_id)
    total = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'data': msg_data, 'total': total})


@common_ajax_response
@lang_translate
def new_seven_data(request):
    """data in a week"""
    msg_code, msg_data = interface.get_new_seven_data()
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def get_name(request):
    """get the notary and client name"""
    data = interface.get_name_list()
    return format_return(0, data=data)


@common_ajax_response
@lang_translate
def distribution_data(request):
    """show the distribution data"""
    msg_code, msg_data = interface.distribution_data()
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def notary_distribution_data(request):
    """show the distribution data of notary"""
    notary_list = request.POST.get('notary_list')
    msg_code, msg_data = interface.notary_distribution_data(notary_list=None)
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def handle_efficiency(request):
    """show the efficiency of handling datacap request """
    notary_list = request.POST.get('notary_list')
    msg_code, msg_data = interface.get_handle_efficiency(notary_list=notary_list)
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def notary_handle_efficiency_borad(request):
    """handling data request board"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    sort_type = request.POST.get('sort_type')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    msg_data = interface.get_handle_efficiency_borad()
    msg_code, msg_data = interface.get_handle_efficiency_borad_sort(sort_type=sort_type, data=msg_data)
    if msg_code != 0:
        return format_return(msg_code)
    length = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'data': msg_data, 'length': length})


@common_ajax_response
@lang_translate
def request_borad(request):
    """show datacap request board"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    sort_type = request.POST.get('sort_type')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    msg_data = interface.get_request_borad()
    msg_code, msg_data = interface.get_request_borad_sort(data=msg_data, sort_type=sort_type)
    if msg_code != 0:
        return format_return(msg_code)
    length = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(msg_code, data={'data': msg_data, 'length': length})


@common_ajax_response
@lang_translate
def provider_borad(request):
    """show the provider board"""
    page_index = request.POST.get('page_index')
    page_size = request.POST.get('page_size')
    sort_type = request.POST.get('sort_type')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    msg_data = interface.get_provider_borad()
    msg_code, msg_data = interface.get_provider_borad_sort(sort_type=sort_type, data=msg_data)
    if msg_code != 0:
        return format_return(msg_code)
    length = len(msg_data)
    msg_data = msg_data[(page_size * (page_index - 1)):page_size * page_index]
    return format_return(0, data={'data': msg_data, 'length': length})


@common_ajax_response
@lang_translate
def user_info(request):
    """show the user info"""
    address = request.POST.get('address')
    msg_code, msg_data = interface.get_user_info(address=address)
    return format_return(msg_code, data=msg_data)


@common_ajax_response
@lang_translate
def assumption_details(request):
    """show the details of assumption"""
    address = request.POST.get('address')
    page_index = request.POST.get('page_index', '1')
    page_size = request.POST.get('page_size', '5')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    msg_code, msg_data = interface.get_assumption_details(address=address)
    obj = Page(msg_data, page_size).page(page_index)
    data_list = []
    for i in obj.get('objects'):
        data_list.append({
            'deal_id': i.deal_id,
            'height_time': i.height_time.strftime('%Y-%m-%d %H:%M:%S'),
            'provider_id': i.provider_id,
            'file_size': i.file_size,
        })
    return format_return(0, data={"objs": data_list, "total_page": obj.get('total_page'),
                                  "total_count": obj.get('total_count')})


@common_ajax_response
@lang_translate
def request_records(request):
    """show the datacap request records"""
    address = request.POST.get('address')
    page_index = request.POST.get('page_index', '1')
    page_size = request.POST.get('page_size', '5')
    page_size = interface.handle_page(page_size, 5)
    page_index = interface.handle_page(page_index, 1)
    msg_code, msg_data = interface.request_record(address=address)
    obj = Page(msg_data, page_size).page(page_index)
    data_list = []
    for i in obj.get('objects'):
        msg_cid = i.msg_cid
        assignee = i.assignee
        comments_url = i.comments_url
        data_list.append({
            'assignee': assignee,
            'created_at': i.created_at.strftime('%Y-%m-%d %H:%M:%S') if i.created_at else i.created_at,
            'region': i.region,
            'request_datacap': i.request_datacap,
            'status': i.status,
            'allocated_datacap': i.allocated_datacap,
            'msg_cid': msg_cid,
            'url': interface.get_req_url(i.comments_url),
            'height': get_height(msg_cid),
            'name': i.name,
            'media': i.media,
            'github_url': get_github_url(comments_url),
            'issue_id': get_api_issue_id(comments_url),
            'notary': get_notary_by_github_account(assignee),
        })
    return format_return(0, data={"objs": data_list, "total_page": obj.get('total_page'),
                                  "total_count": obj.get('total_count')})


@common_ajax_response
@lang_translate
def region_disribution_rate(request):
    """show the rate of the distribution in regions"""
    sort_type = request.POST.get('sort_type')
    data = interface.get_region_disribution_rate(sort_type=sort_type)
    return format_return(data[0], data=data[1])


@common_ajax_response
@lang_translate
def region_notary_disribution_rate(request):
    """show the rate of the distribution of notaries in a region"""
    sort_type = request.POST.get('sort_type')
    region = request.POST.get('region')
    data = interface.get_region_notary_disribution_rate(sort_type=sort_type, region=region)
    return format_return(data[0], data=data[1])


# cron jobs
@common_ajax_response
@lang_translate
def get_req_record(request):
    """record datacap request"""
    initial_req()
    return format_return(0)


@common_ajax_response
@lang_translate
def get_msg_data(request):
    """get msg cid and details"""
    get_msg_cid()
    return format_return(0)


@common_ajax_response
@lang_translate
def get_deal_info(request):
    """get deal info"""
    get_deal_data()
    return format_return(0)


@common_ajax_response
@lang_translate
def refresh_data(request):
    """refresh redis data"""
    refresh_data_now()
    return format_return(0)


@common_ajax_response
@lang_translate
def get_address(request):
    """record github apply address"""
    get_unkown_address()
    return format_return(0)


@common_ajax_response
@lang_translate
def check_closed_issue(request):
    """check if issues has closed"""
    get_check_closed_issue()
    return format_return(0)
