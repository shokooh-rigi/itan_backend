from django import template

from mysite.estimator.templatetags.estimator_tags import estimate_total_calculator
from mysite.order.templatetags.order_tags import order_total_calculator
from mysite.proposal.models import Proposal
from ...order.models import Order

register = template.Library()


@register.simple_tag
def total_quoted_count(customer, from_date_obj, to_date_obj):
    quoted_count = Proposal.objects.filter(
        estimate__customer__company=customer,
        created_on__range=(from_date_obj, to_date_obj),
    ).count()
    return quoted_count


@register.simple_tag
def total_quoted_price(customer, from_date_obj, to_date_obj):
    total_quote = 0
    quote_list = Proposal.objects.filter(
        estimate__customer__company=customer,
        created_on__range=(from_date_obj, to_date_obj),
    )
    for quote in quote_list:
        total_quote = total_quote + estimate_total_calculator(quote.estimate.id)
    return total_quote


@register.simple_tag
def total_ordered_count(customer, from_date_obj, to_date_obj):
    ordered_count = Order.objects.filter(
        proposal__estimate__customer__company=customer,
        proposal__created_on__range=(from_date_obj, to_date_obj),
    ).count()
    return ordered_count


@register.simple_tag
def total_ordered_price(customer, from_date_obj, to_date_obj):
    total_order = 0
    order_list = Order.objects.filter(
        proposal__estimate__customer__company=customer,
        proposal__created_on__range=(from_date_obj, to_date_obj),
    )
    for order in order_list:
        total_order = total_order + order_total_calculator(
            order.proposal.estimate.id, order
        )
    return total_order


@register.simple_tag
def performance(customer, from_date_obj, to_date_obj):
    quoted_count = Proposal.objects.filter(
        estimate__customer__company=customer,
        created_on__range=(from_date_obj, to_date_obj),
    ).count()
    ordered_count = Order.objects.filter(
        proposal__estimate__customer__company=customer,
        proposal__created_on__range=(from_date_obj, to_date_obj),
    ).count()
    customer_performance = int((ordered_count / quoted_count) * 100)
    return customer_performance
