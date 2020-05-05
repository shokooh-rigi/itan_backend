from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator
from ..models import ChangeOrder

register = template.Library()


@register.simple_tag
def order_total_calculator(estimate_id, order):
    estimate_total = estimate_total_calculator(estimate_id)
    change_orders = ChangeOrder.objects.filter(order=order)
    co_total = 0
    for change_order in change_orders:
        co_total = co_total + change_order.amount
    order_total = float(estimate_total.replace(',', '')) + float(co_total)
    order_total = round(order_total, 2)
    return order_total


@register.simple_tag
def calculate_total_amount_due(invoice):
    sub_total = order_total_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    completed_percentage = invoice.percent_of_performance_completed
    received_to_date = float(invoice.total_payment_received_to_date)
    past_amount = float(invoice.past_due_amount)
    total = (sub_total * completed_percentage / 100)
    total = total - received_to_date + past_amount
    return '{0:,.2f}'.format(total)
