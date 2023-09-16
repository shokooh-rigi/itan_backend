from django import template
import random
from ..models import Estimate, EstimateEquipment
from ...order.models import ChangeOrder
from ...s3_file_manager import S3
from ...submittal.forms import CompanySubmittal

register = template.Library()


@register.simple_tag
def estimate_number_generator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimator_long_id = estimate.created_by.id + 100
    estimate_date_created = str(estimate.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(estimate.id).zfill(3)


@register.simple_tag
def submittal_number_generator(submittal_id):
    submittal = CompanySubmittal.objects.get(id=submittal_id)
    submittal_long_id = submittal.created_by.id + 100
    submittal_date_created = str(submittal.created_on).replace('-', '')[2:8]
    return submittal_date_created + str(submittal_long_id) + str(submittal.id).zfill(3)


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def pdf_filename_generator(estimate_id, pdf_type, version=None):
    estimate = Estimate.objects.get(id=estimate_id)
    longidname = estimate_number_generator(estimate_id)
    estimate_version = ''
    if version:
        estimate_version = '_' + str(version)
    estimate_filename = pdf_type + longidname + '_' + estimate.project.name + estimate_version
    return estimate_filename \
        .replace(' ', '_') \
        .replace('!', '') \
        .replace('@', '') \
        .replace('#', '') \
        .replace('$', '') \
        .replace('%', '') \
        .replace('^', '') \
        .replace('&', '') \
        .replace('*', '') \
        .replace("/", '')


@register.simple_tag
def changeorder_filename_generator(co_id):
    co = ChangeOrder.objects.get(id=co_id)

    new_file_name = 'ChangeOrder-' + str(co.order.project_number[3:]).zfill(3) + '-' + co.co_number
    return new_file_name \
        .replace(' ', '_') \
        .replace('!', '') \
        .replace('@', '') \
        .replace('#', '') \
        .replace('$', '') \
        .replace('%', '') \
        .replace('^', '') \
        .replace('&', '') \
        .replace('*', '') \
        .replace("/", '')


@register.simple_tag
def equipment_total_calculator(equipment):
    if equipment.price_override:
        return float(equipment.price_override) * float(equipment.quantity)
    else:
        return float(equipment.equipment.price) * float(equipment.quantity)


@register.simple_tag
def service_total_calculator(service, estimate_equipments_pricing):
    service_total = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        if estimate_equipment_pricing.equipment.service == service:
            if estimate_equipment_pricing.price_override:
                service_total = service_total + float(estimate_equipment_pricing.price_override) \
                                * float(estimate_equipment_pricing.quantity)
            else:
                service_total = service_total + float(estimate_equipment_pricing.equipment.price) \
                                * float(estimate_equipment_pricing.quantity)
    return service_total


@register.simple_tag
def estimate_sub_total_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        equipment_total = equipment_total_calculator(estimate_equipment_pricing)
        estimate_sub += float(equipment_total)

    control_system_calculated = round((estimate_sub * (1 + estimate.estimatedetails.control_system / 100)) - estimate_sub, 2)
    hours_calculated = round((estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub, 2)
    estimate_total = estimate_sub + control_system_calculated + hours_calculated + float(estimate.estimatedetails.adjustment)
    estimate_total = round(estimate_total, 2)
    return estimate_total


@register.simple_tag
def estimate_sub_total_dalt_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)\
        .filter(equipment__service__name__iexact="DALT")
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        equipment_total = equipment_total_calculator(estimate_equipment_pricing)
        estimate_sub += float(equipment_total)

    estimate_total = estimate_sub
    estimate_total = round(estimate_total, 2)
    return estimate_total


@register.simple_tag
def estimate_sub_total_exclude_dalt_calculator(estimate_id):
    sub_total = estimate_sub_total_calculator(estimate_id)
    dalt_total = estimate_sub_total_dalt_calculator(estimate_id)
    estimate_total = round(sub_total - dalt_total, 2)
    return estimate_total


@register.simple_tag
def estimate_predemo_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    predemo_calculated = estimate.estimatedetails.pre_demo * 1200
    return predemo_calculated


@register.simple_tag
def estimate_customer_adjustment_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    sub_total = estimate_sub_total_calculator(estimate_id) + estimate_predemo_calculator(estimate_id)
    customer_adjustment = (estimate.customer.company.customer_adjustment_in_percentage * sub_total / 100)
    return customer_adjustment


@register.simple_tag
def estimate_total_calculator(estimate_id):
    estimate_sub_total = estimate_sub_total_calculator(estimate_id)
    pre_demo = estimate_predemo_calculator(estimate_id)
    customer_adjustment = estimate_customer_adjustment_calculator(estimate_id)
    estimate_total = float(estimate_sub_total) + float(pre_demo) + float(customer_adjustment)
    estimate_total = round(estimate_total, 2)
    return estimate_total


@register.simple_tag
def estimate_total_minus_predemo_calculator(estimate_id):
    estimate_total = estimate_total_calculator(estimate_id)
    pre_demo_total = estimate_predemo_calculator(estimate_id)
    return estimate_total - pre_demo_total


@register.simple_tag
def estimate_total_minus_predemo_minus_dalt_calculator(estimate_id):
    estimate_total = estimate_total_calculator(estimate_id)
    pre_demo_total = estimate_predemo_calculator(estimate_id)
    dalt_total = estimate_sub_total_dalt_calculator(estimate_id)
    return estimate_total - pre_demo_total - dalt_total


@register.filter
def in_setting(things, key):
    return things.filter(key=key)


@register.filter
def get_item(dictionary, key):
    if dictionary:
        if dictionary.get(key):
            return dictionary.get(key)
        else:
            return ''
    else:
        return ''


@register.filter
def get_list(dictionary, key):
    if dictionary:
        if dictionary[key]:
            return dictionary[key]
        else:
            return ''


@register.simple_tag
def random_int(a, b=None):
    if b is None:
        a, b = 0, a
    return random.randint(a, b)


@register.simple_tag
def get_s3_file_url(key, pdf_type, version=None):
    s3 = S3()
    if pdf_type == 'estimate':
        return s3.get_bucket_object(key='media/pdfs/estimate/' + pdf_filename_generator(key, 'E', version) + '.pdf')
    if pdf_type == 'quote':
        return s3.get_bucket_object(key='media/pdfs/quote/' + pdf_filename_generator(key, 'Q') + '.pdf')
    if pdf_type == 'proposal':
        return s3.get_bucket_object(key='media/pdfs/proposal/' + pdf_filename_generator(key, 'P') + '.pdf')
    if pdf_type == 'changeorder':
        return s3.get_bucket_object(key='media/pdfs/changeorder/' + changeorder_filename_generator(key) + '.pdf')
    if pdf_type == 'invoice':
        return s3.get_bucket_object(key='media/pdfs/invoice/' + key + '.pdf')
    if pdf_type == 'account_summary':
        return s3.get_bucket_object(key='media/pdfs/accountsummary/AccountSummary-' + key + '.pdf')
    if pdf_type == 'submittal':
        return s3.get_bucket_object(key='media/pdfs/submittal/submittal-' + submittal_number_generator(key) + '.pdf')
    if pdf_type == 'report':
        return s3.get_bucket_object(key='media/pdfs/report/FINAL SHEET ' + key.project.proposal.quote.estimate.project.name.upper() + '-' + str(key.project.project_number) + '.pdf')
    else:
        return s3.get_bucket_object(key='media/' + str(key))
