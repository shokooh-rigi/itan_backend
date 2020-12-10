from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator
from ..models import ChangeOrder
from ...gi.models import InvoiceTransaction

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
    total = (sub_total * completed_percentage / 100)
    total = total
    return '{0:,.2f}'.format(total)


@register.simple_tag
def calculate_total_paid(invoice):
    transactions = InvoiceTransaction.objects.filter(invoice=invoice)
    total = 0
    for transaction in transactions:
        total += transaction.amount
    return '{0:,.2f}'.format(total)


@register.simple_tag
def calculate_remaining_invoice_due(invoice):
    transactions = InvoiceTransaction.objects.filter(invoice=invoice)
    total_paid = 0
    for transaction in transactions:
        total_paid += transaction.amount

    sub_total = order_total_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    completed_percentage = invoice.percent_of_performance_completed
    total = (sub_total * completed_percentage / 100)
    total = total
    remaining = float(total) - float(total_paid)
    return remaining
