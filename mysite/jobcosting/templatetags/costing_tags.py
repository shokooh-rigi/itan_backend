from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator
from ...order.models import EstimateEquipment
from ...gi.models import InvoiceTransaction
from ...scheduler.models import Schedule, Maintenance
from ...order.templatetags.order_tags import calculate_total_amount_due

register = template.Library()


@register.simple_tag
def estimate_total_work(estimate_id):
    estimate_equipments = EstimateEquipment.objects.filter(estimate=estimate_id, flag=True)
    estimate_work = 0
    for each_estimate_equipment in estimate_equipments:
        work_total = int(each_estimate_equipment.quantity) * int(each_estimate_equipment.equipment.estimate_work)
        estimate_work += int(work_total)
    estimate_work = estimate_work/60
    return estimate_work


@register.simple_tag
def actual_total_work(order_id):
    schedules = Schedule.objects.filter(order_id=order_id)
    maintenances = Maintenance.objects.filter(order__id=order_id)
    actual_work = 0
    for schedule in schedules:
        work_total = schedule.schedule_end - schedule.schedule_start
        actual_work += int(work_total.total_seconds())
    for maintenance in maintenances:
        work_total = maintenance.schedule_end - maintenance.schedule_start
        actual_work += int(work_total.total_seconds())
    actual_work = actual_work/3600
    return actual_work


@register.simple_tag
def delta_total_work(order):
    etw = estimate_total_work(order.proposal.quote.estimate.id)
    atw = actual_total_work(order.id)
    if atw > 0:
        delta = (atw - etw) / atw * 100
    else:
        delta = 0
    return delta


@register.simple_tag
def delta_total_price(order):
    etp = estimate_total_calculator(order.proposal.quote.estimate.id)
    atp = calculate_total_amount_due(order.invoice)
    if atp > 0:
        delta = (atp - etp) / atp * 100
    else:
        delta = 0
    return delta
