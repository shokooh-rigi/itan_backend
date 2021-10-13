from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator, estimate_predemo_calculator
from ..models import ChangeOrder, EstimateEquipment
from ...gi.models import InvoiceTransaction, InvoiceHistory
from ...scheduler.models import Schedule, Maintenance

register = template.Library()


@register.simple_tag
def order_total_calculator(estimate_id, order):
    estimate_total = estimate_total_calculator(estimate_id)
    change_orders = ChangeOrder.objects.filter(order=order)
    co_total = 0
    for change_order in change_orders:
        co_total = co_total + change_order.amount
    order_total = float(estimate_total) + float(co_total)
    order_total = round(order_total, 2)
    return order_total


@register.simple_tag
def order_predemo_calculator(estimate_id, order):
    predemo_calc = estimate_predemo_calculator(estimate_id)
    return predemo_calc


@register.simple_tag
def order_final_calculator(estimate_id, order):
    otc = order_total_calculator(estimate_id, order)
    opc = order_predemo_calculator(estimate_id, order)
    return otc - opc


@register.simple_tag
def order_tech_predemo_price_calculator(estimate_id, order):
    opc = order_predemo_calculator(estimate_id, order)
    order_offset = order.predemo_offset
    tech_price = float(opc) - float(order_offset)
    return tech_price


@register.simple_tag
def order_tech_final_price_calculator(estimate_id, order):
    ofc = order_final_calculator(estimate_id, order)
    order_offset = order.final_offset
    tech_price = float(ofc) - float(order_offset)
    return tech_price


@register.simple_tag
def calculate_total_amount_due(invoice):
    if invoice.invoice_type == 1:
        sub_total = order_total_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    elif invoice.invoice_type == 2:
        sub_total = order_predemo_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    else:
        sub_total = order_final_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
    completed_percentage = invoice.percent_of_performance_completed
    total = (sub_total * completed_percentage / 100)
    return total


@register.simple_tag
def calculate_total_paid(invoice):
    transactions = InvoiceTransaction.objects.filter(invoice=invoice)
    total = 0
    for transaction in transactions:
        total += transaction.amount
    return total


@register.simple_tag
def calculate_remaining_invoice_due(invoice):
    transactions = InvoiceTransaction.objects.filter(invoice=invoice)
    total_paid = 0
    for transaction in transactions:
        total_paid += transaction.amount

    total = calculate_total_amount_due(invoice)
    remaining = float(total) - float(total_paid)
    return remaining


@register.simple_tag
def get_last_invoice_history(invoice):
    lih = InvoiceHistory.objects.filter(invoice=invoice).order_by('created_on').last
    return lih
