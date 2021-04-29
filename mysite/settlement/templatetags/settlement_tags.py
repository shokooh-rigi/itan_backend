from django import template

from ..models import SettledSchedule, Schedule, Order, ScheduleTech, SettledMaintenances
from ...order.templatetags.order_tags import order_total_calculator
from ...estimator.templatetags.estimator_tags import estimate_predemo_calculator
register = template.Library()


@register.simple_tag
def calculate_settlement_amount(settled_order):
    settled_amount = settled_order.settled_value * settled_order.settlement.contractor.profile.interest_percentage / 100
    return settled_amount


@register.simple_tag
def calculate_total_settled(settlement):
    settled_orders = SettledSchedule.objects.filter(settlement=settlement)
    settled_maintenances = SettledMaintenances.objects.filter(settlement=settlement)
    total = 0
    for settled_order in settled_orders:
        total = total + settled_order.settled_value
    for settled_maintenance in settled_maintenances:
        total = total + settled_maintenance.settled_value
    return total


@register.simple_tag
def calculate_total_settled_including_expenses(settlement):
    total_settled = calculate_total_settled(settlement) + settlement.fixed_expenses
    return total_settled


@register.simple_tag
def order_quote_price(schedule):
    if schedule.order.proposal.quote.estimate.estimatedetails.pre_demo > 0:
        if schedule.pre_demo:
            total = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
        else:
            pre_demo_price = estimate_predemo_calculator(schedule.order.proposal.quote.estimate.id)
            order_price = order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order)
            total = order_price - pre_demo_price
    else:
        total = order_total_calculator(schedule.order.proposal.quote.estimate.id, schedule.order)
    return total


@register.simple_tag
def tech_involvement(schedule, contractor):
    return ScheduleTech.objects.get(schedule=schedule, assigned_to_contractor=contractor).involvement_percentage
