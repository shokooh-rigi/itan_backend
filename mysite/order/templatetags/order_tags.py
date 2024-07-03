from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator, estimate_predemo_calculator, estimate_sub_total_dalt_calculator
from ..models import ChangeOrder, EstimateEquipment, ChangeOrderService
from ...gi.models import InvoiceTransaction, InvoiceHistory, Setting, Invoice
from ...scheduler.models import Schedule, Maintenance
import datetime
from django.utils import timezone
from datetime import timedelta


register = template.Library()


@register.simple_tag
def change_order_total_calculator(change_order_id):
    change_order = ChangeOrder.objects.get(id=change_order_id)
    change_order_services = ChangeOrderService.objects.filter(change_order=change_order)
    co_total = 0
    for change_order_service in change_order_services:
        co_total += change_order_service.amount
    return co_total


@register.simple_tag
def order_total_calculator(estimate_id, order):
    estimate_total = estimate_total_calculator(estimate_id)
    change_orders = ChangeOrder.objects.filter(order=order)
    approved_change_orders = change_orders.filter(confirmed=True)
    cos_total = 0
    for change_order in approved_change_orders:
        cos_total += change_order_total_calculator(change_order.id)
    order_total = float(estimate_total) + float(cos_total)
    order_total = round(order_total, 2)
    return order_total


@register.simple_tag
def order_predemo_calculator(estimate_id, order):
    predemo_calc = estimate_predemo_calculator(estimate_id)
    return predemo_calc


@register.simple_tag
def order_dalt_calculator(estimate_id, order):
    dalt_calc = estimate_sub_total_dalt_calculator(estimate_id)
    return dalt_calc


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
    elif invoice.invoice_type == 4:
        sub_total = order_dalt_calculator(invoice.order.proposal.quote.estimate.id, invoice.order)
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


@register.simple_tag
def get_full_address(project):
    full_address = ''
    if project.address_line_1:
        full_address += project.address_line_1
    if project.address_line_2:
        full_address += ' ' + project.address_line_2
    if project.city:
        full_address += ' ' + project.city
    if project.state:
        full_address += ' ' + project.state
    if project.zip:
        full_address += ' ' + project.zip
    return full_address


@register.simple_tag
def co_total_amount(co):
    all_services = ChangeOrderService.objects.filter(change_order=co)
    total = 0
    for service in all_services:
        total += service.amount
    return total


@register.simple_tag
def past_30_days(order):
    if len(Invoice.objects.filter(order=order)) > 0:
        overdue_days = Setting.objects.get(key='Overdue Days').value
        overdue_datetime = timezone.now() - timedelta(days=int(overdue_days))
        created_on_aware = order.invoice.created_on
        if created_on_aware < overdue_datetime:
            return True
        return False
    return None


@register.filter
def enumerate_list(value):
    return enumerate(value)

