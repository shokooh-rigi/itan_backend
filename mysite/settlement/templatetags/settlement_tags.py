from django import template

from ..models import SettledSchedule, SettledMaintenances
from ...estimator.templatetags.estimator_tags import estimate_predemo_calculator
from ...order.templatetags.order_tags import order_total_calculator
from ...scheduler.models import ScheduleTech

register = template.Library()


@register.simple_tag
def calculate_settlement_amount(settled_order):
    settled_amount = (
        settled_order.settled_value
        * settled_order.settlement.contractor.profile.interest_percentage
        / 100
    )
    return settled_amount


@register.simple_tag
def calculate_total_settled(settlement):
    settled_orders = SettledSchedule.objects.filter(settlement=settlement)
    settled_maintenances = SettledMaintenances.objects.filter(settlement=settlement)
    total = 0
    for settled_order in settled_orders:
        if settled_order.settle_override:
            total = total + settled_order.settle_override
        else:
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
    if schedule.order.proposal.estimate.estimatedetails.pre_demo > 0:
        if schedule.pre_demo:
            total = estimate_predemo_calculator(schedule.order.proposal.estimate.id)
            predemo_offset = float(schedule.order.predemo_offset)
            total = total - predemo_offset
        else:
            pre_demo_price = estimate_predemo_calculator(
                schedule.order.proposal.estimate.id
            )
            order_price = order_total_calculator(
                schedule.order.proposal.estimate.id, schedule.order
            )
            final_offset = float(schedule.order.final_offset)
            print(final_offset)
            total = order_price - pre_demo_price - final_offset
    else:
        total = order_total_calculator(
            schedule.order.proposal.estimate.id, schedule.order
        )
        offset = float(schedule.order.final_offset)
        total = total - offset
    return total


@register.simple_tag
def tech_involvement(schedule, contractor):
    return ScheduleTech.objects.get(
        schedule=schedule, assigned_to=contractor
    ).involvement_percentage


@register.simple_tag
def previous_payment_calc(settled_schedule):
    return (
        float(settled_schedule.previous_payment)
        * float(settled_schedule.settlement.contractor.profile.interest_percentage)
        / 100
    )
