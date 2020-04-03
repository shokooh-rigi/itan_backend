from django import template
from ..models import SettledOrders

register = template.Library()


@register.simple_tag
def calculate_total_settled(settlement):
    settled_orders = SettledOrders.objects.filter(settlement=settlement)
    total = 0
    for settled_order in settled_orders:
        total = total + settled_order.settled_value
    return total
