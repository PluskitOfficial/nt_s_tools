from django.conf.urls import url

from tools.views import show_notary_info_list, notary_region_rate, query_msg, new_seven_data, \
    distribution_data, notary_distribution_data, handle_efficiency, notary_handle_efficiency_borad, request_borad, \
    provider_borad, user_info, assumption_details, request_records, notary_info, notary_req, get_req_record, \
    get_msg_data, get_deal_info, provider_info_basic_info, provider_info_order_stat, provider_info_order_details_list, \
    refresh_data, get_address, check_closed_issue, region_disribution_rate, region_notary_disribution_rate, \
    provider_info_client_list, get_name

urlpatterns = [
    url(r'^show_notary_info_list$', show_notary_info_list),
    url(r'^notary_region_rate$', notary_region_rate),
    url(r'^query_msg$', query_msg),
    url(r'^provider_info_basic_info$', provider_info_basic_info),
    url(r'^provider_info_order_stat$', provider_info_order_stat),
    url(r'^provider_info_order_details_list$', provider_info_order_details_list),
    url(r'^provider_info_client_list$', provider_info_client_list),
    url(r'^new_seven_data$', new_seven_data),
    url(r'^distribution_data$', distribution_data),
    url(r'^notary_distribution_data$', notary_distribution_data),
    url(r'^handle_efficiency$', handle_efficiency),
    url(r'^notary_handle_efficiency_borad$', notary_handle_efficiency_borad),
    url(r'^request_borad$', request_borad),
    url(r'^provider_borad$', provider_borad),
    url(r'^user_info$', user_info),
    url(r'^assumption_details$', assumption_details),
    url(r'^request_records$', request_records),
    url(r'^notary_info$', notary_info),
    url(r'^notary_req$', notary_req),
    url(r'^region_disribution_rate$', region_disribution_rate),
    url(r'^region_notary_disribution_rate$', region_notary_disribution_rate),
    url(r'^get_name$', get_name),

    # cron job
    url(r'^get_req_record$', get_req_record),
    url(r'^get_msg_data$', get_msg_data),
    url(r'^get_deal_info$', get_deal_info),
    url(r'^refresh_data$', refresh_data),
    url(r'^get_address$', get_address),
    url(r'^check_closed_issue$', check_closed_issue),
]
