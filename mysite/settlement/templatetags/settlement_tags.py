from django import template

from ..models import SettledOrders

register = template.Library()


@register.simple_tag
def calculate_settlement_amount(settled_order):
    settled_amount = settled_order.settled_value * settled_order.settlement.contractor.company.interest_percentage / 100
    return settled_amount


@register.simple_tag
def calculate_total_settled(settlement):
    settled_orders = SettledOrders.objects.filter(settlement=settlement)
    total = 0
    for settled_order in settled_orders:
        total = total + settled_order.settled_value
    return total


@register.simple_tag
def calculate_total_settled_including_expenses(settlement):
    settled_orders = SettledOrders.objects.filter(settlement=settlement)
    total = 0
    for settled_order in settled_orders:
        total = total + settled_order.settled_value
    total = total + settlement.fixed_expenses
    return total
