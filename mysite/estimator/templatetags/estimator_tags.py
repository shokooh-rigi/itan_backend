from django import template
from ..forms import *

register = template.Library()


@register.simple_tag
def url_replace(request, field, value):

    dict_ = request.GET.copy()

    dict_[field] = value

    return dict_.urlencode()


@register.simple_tag
def estimate_number_generator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimator_long_id = estimate.created_by.id + 100
    estimate_date_created = str(estimate.created_on).replace('-', '')[2:8]
    return estimate_date_created + str(estimator_long_id) + str(estimate.id).zfill(3)


@register.simple_tag
def pdf_filename_generator(estimate_id, pdf_type):
    estimate = Estimate.objects.get(id=estimate_id)
    longidname = estimate_number_generator(estimate_id)
    return pdf_type + longidname + '_' + estimate.project.name.replace(' ', '_')


@register.simple_tag
def equipment_total_calculator(equipment):
    if equipment.price_override:
        return '{0:.2f}'.format(float(equipment.price_override) * float(equipment.quantity))
    else:
        return '{0:.2f}'.format(float(equipment.equipment.price) * float(equipment.quantity))


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
    return '{0:.2f}'.format(service_total)


@register.simple_tag
def estimate_sub_total_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    estimate_equipments_pricing = EstimateEquipment.objects.filter(estimate=estimate_id)
    estimate_sub = 0
    for estimate_equipment_pricing in estimate_equipments_pricing:
        equipment_total = equipment_total_calculator(estimate_equipment_pricing)
        estimate_sub += float(equipment_total)

    control_system_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.control_system / 100)) - estimate_sub, 2)
    hours_calculated = round(
        (estimate_sub * (1 + estimate.estimatedetails.hours / 100)) - estimate_sub, 2)
    estimate_total = estimate_sub + control_system_calculated + hours_calculated \
                     + float(estimate.estimatedetails.adjustment)
    estimate_total = round(estimate_total, 2)
    return '{0:.2f}'.format(estimate_total)


@register.simple_tag
def estimate_predemo_calculator(estimate_id):
    estimate = Estimate.objects.get(id=estimate_id)
    predemo_calculated = estimate.estimatedetails.pre_demo * 1200
    return '{0:.2f}'.format(predemo_calculated)


@register.simple_tag
def estimate_total_calculator(estimate_id):
    estimate_sub_total = estimate_sub_total_calculator(estimate_id)
    predemo = estimate_predemo_calculator(estimate_id)
    estimate_total = float(estimate_sub_total) + float(predemo)
    estimate_total = round(estimate_total, 2)
    return '{0:.2f}'.format(estimate_total)


@register.filter
def in_setting(things, key):
    return things.filter(key=key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
