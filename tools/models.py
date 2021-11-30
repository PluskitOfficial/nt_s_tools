from django.db import models
import json


class Notaries(models.Model):
    name = models.CharField(verbose_name='notary name', max_length=64)
    github_account = models.CharField(verbose_name='notary github name', max_length=32)
    github_accounts_dict = models.JSONField(verbose_name='notary github name dict', default=dict)
    address = models.CharField(verbose_name='notary address', max_length=128)
    id_address = models.CharField(verbose_name='notary id', max_length=16, null=True)
    media = models.CharField(verbose_name='social media', max_length=128)
    use_case = models.JSONField(verbose_name='reason of applying as a notary')
    application_link = models.CharField(verbose_name='application link', max_length=256)

    region = models.CharField(verbose_name='region of the notary', max_length=128)
    granted_date = models.DateField(verbose_name='granted date')
    granted_allowance = models.DecimalField(verbose_name='datacap owned', max_digits=32, decimal_places=0)
    allowance = models.DecimalField(verbose_name='datacap distributed', max_digits=32, decimal_places=0, null=True)
    refuse_allowance = models.DecimalField(verbose_name='refused datacap', max_digits=32, decimal_places=0, null=True)

    flag = models.SmallIntegerField(verbose_name='flag ', default=1)

    create_time = models.DateTimeField(verbose_name='record time', auto_now_add=True)

    class meta:
        ordering = ['-create_time']


class NotariesWallet(models.Model):
    notary = models.ForeignKey(to='Notaries', verbose_name='notary', related_name='wallet', on_delete=models.DO_NOTHING)
    address = models.CharField(verbose_name='address', max_length=128)
    flag = models.SmallIntegerField(verbose_name='flag', default=1)
    create_time = models.DateTimeField(verbose_name='record time', auto_now_add=True)

    class meta:
        ordering = ['-create_time']


class RequestAllowanceRecord(models.Model):
    status_choice = ((0, 'closed but not distributed'), (1, 'handling'), (2, 'distributed'))

    name = models.CharField(verbose_name='assignor name', max_length=256)
    region = models.CharField(verbose_name='region', max_length=32, null=True)
    media = models.CharField(verbose_name='media', max_length=256)
    assignor = models.CharField(verbose_name='assignor', max_length=32, db_index=True)
    assignee = models.CharField(verbose_name='assignee', max_length=32, null=True, db_index=True)
    apply_address = models.CharField(verbose_name='apply address', max_length=128, null=True)
    allocated_address = models.CharField(verbose_name='allocated address', max_length=128, null=True)
    status = models.SmallIntegerField(verbose_name='status', db_index=True)
    created_at = models.DateTimeField(verbose_name='issue create time')
    closed_at = models.DateTimeField(verbose_name='issue close time', null=True)
    updated_at = models.DateTimeField(verbose_name='issue update time')
    comments_url = models.CharField(verbose_name='comments_url', max_length=256)
    msg_cid = models.CharField(verbose_name='msg cid', max_length=128, null=True, db_index=True)
    allocated_datacap = models.DecimalField(verbose_name='allocated amount', max_digits=32, decimal_places=0, null=True)
    request_datacap = models.DecimalField(verbose_name='request amount', max_digits=32, decimal_places=0, null=True)
    distribute_date = models.DateField(verbose_name='distribute date', null=True, db_index=True)

    flag = models.IntegerField(verbose_name='flag', default=1, db_index=True)
    create_time = models.DateTimeField(verbose_name='record time', auto_now_add=True)

    class meta:
        ordering = ['-create_time']


class MessageDetails(models.Model):
    id = models.BigAutoField(primary_key=True)

    msg_cid = models.CharField(verbose_name='msg cid', max_length=128, db_index=True)
    height = models.IntegerField(verbose_name='height')
    height_time = models.DateTimeField(verbose_name='time')

    msg_from = models.CharField(verbose_name='msg from', max_length=128, db_index=True)
    msg_to = models.CharField(verbose_name='msg to', max_length=128)
    msg_method = models.IntegerField(verbose_name='method')
    msg_method_name = models.CharField(verbose_name='method name', max_length=32, db_index=True)
    msg_value = models.DecimalField(verbose_name='msg value', max_digits=32, decimal_places=0)
    msgrct_exit_code = models.IntegerField(verbose_name='msg code')

    gascost_miner_penalty = models.DecimalField(verbose_name='gascost_miner_penalty', max_digits=32, decimal_places=0)
    gascost_refund = models.DecimalField(verbose_name='gascost_refund', max_digits=32, decimal_places=0)
    gascost_base_fee_burn = models.DecimalField(verbose_name='base fee burn', max_digits=32, decimal_places=0)
    gascost_total_cost = models.DecimalField(verbose_name='base fee burn', max_digits=32, decimal_places=0)
    gascost_miner_tip = models.DecimalField(verbose_name='storage provider tip', max_digits=32, decimal_places=0)
    gascost_over_estimation_burn = models.DecimalField(verbose_name='over estimation burn', max_digits=32,
                                                       decimal_places=0)
    msg_nonce = models.IntegerField(verbose_name='nonce')
    msg_gas_fee_cap = models.DecimalField(verbose_name='gas fee cap', max_digits=32, decimal_places=0)
    msg_gas_premium = models.DecimalField(verbose_name='gas premium', max_digits=32, decimal_places=0)
    msg_gas_limit = models.DecimalField(verbose_name='gas limit', max_digits=32, decimal_places=0)
    gascost_gas_used = models.DecimalField(verbose_name='gas used', max_digits=32, decimal_places=0)
    base_fee = models.DecimalField(verbose_name='base fee', max_digits=32, decimal_places=0)

    msg_return = models.JSONField(verbose_name='msg return', null=True)
    msg_params = models.JSONField(verbose_name='msg params', null=True)

    status = models.IntegerField(verbose_name='status', null=True)

    msg_date = models.DateField(verbose_name='msg date', null=True)
    create_time = models.DateTimeField(verbose_name='record time', auto_now_add=True)

    class meta:
        ordering = ['-height_time', '-create_time']


class TransactionRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    provider_id = models.CharField(verbose_name='provider id', max_length=128, db_index=True)
    provider_address = models.CharField(verbose_name='provider address', max_length=64, null=True)
    client_address = models.CharField(verbose_name='client address', max_length=128, db_index=True)
    file_size = models.DecimalField(verbose_name='file size', max_digits=32, decimal_places=0)
    height_time = models.DateTimeField(verbose_name='order time', null=True, db_index=True)
    height = models.IntegerField(verbose_name='height', null=True)
    is_verified = models.IntegerField(verbose_name='is_verified', default=0)
    order_date = models.DateField(verbose_name='order_date', null=True, db_index=True)
    deal_id = models.CharField(verbose_name='deal_id', max_length=16, db_index=True)

    create_time = models.DateTimeField(verbose_name='record time', auto_now_add=True)

    class meta:
        ordering = ['-height_time', '-create_time']
