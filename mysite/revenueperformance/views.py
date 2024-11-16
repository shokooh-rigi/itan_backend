from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from mysite.estimator.models import *
from ..order.templatetags.order_tags import *
from mysite.estimator.views import estimate_total_calculator
from mysite.order.models import Order
from mysite.gi.models import *
from django.conf import settings
from ..scheduler.models import Schedule, Maintenance
from django.db.models import Q


def is_num(data):
    try:
        int(data)
        return True
    except ValueError:
        return False


@login_required
def revenue_list(request):
    object_list = ''

    from_date_1 = request.GET.get("fromDate1")
    to_date_1 = request.GET.get("toDate1")
    from_date_obj_1 = ''
    to_date_obj_1 = ''
    from_date_2 = request.GET.get("fromDate2")
    to_date_2 = request.GET.get("toDate2")
    from_date_obj_2 = ''
    to_date_obj_2 = ''
    quote_total_1 = 0
    order_total_1 = 0
    invoice_total_1 = 0
    receive_total_1 = 0
    receivable_total_1 = 0
    quote_total_2 = 0
    order_total_2 = 0
    invoice_total_2 = 0
    receive_total_2 = 0
    receivable_total_2 = 0
    quote_total_performance = 0
    order_total_performance = 0
    invoice_total_performance = 0
    receive_total_performance = 0
    receivable_total_performance = 0

    from_date_is_greater = False
    from_date_is_greater_2 = False
    if from_date_1 and to_date_1:
        from_date_obj_1 = datetime.datetime.strptime(from_date_1, '%m/%d/%Y')
        to_date_obj_1 = datetime.datetime.strptime(to_date_1, '%m/%d/%Y')
        to_date_obj_1 = to_date_obj_1 + datetime.timedelta(hours=23, minutes=59, seconds=59)
        if from_date_obj_1 > to_date_obj_1:
            from_date_is_greater = True

        object_list = Quote.objects.filter(created_on__range=(from_date_obj_1, to_date_obj_1))
        for obj in object_list:
            quote_total_1 = quote_total_1 + estimate_total_calculator(obj.estimate.id)

        object_list = Order.objects.filter(created_on__range=(from_date_obj_1, to_date_obj_1))
        for obj in object_list:
            order_total_1 = order_total_1 + order_total_calculator(obj.proposal.estimate.id, obj)

        object_list = Invoice.objects.filter(created_on__range=(from_date_obj_1, to_date_obj_1))
        for obj in object_list:
            invoice_total_1 = invoice_total_1 + calculate_total_amount_due(obj)
            receive_total_1 = receive_total_1 + calculate_total_paid(obj)
            receivable_total_1 = receivable_total_1 + calculate_remaining_invoice_due(obj)

        if from_date_2 and to_date_2:
            from_date_obj_2 = datetime.datetime.strptime(from_date_2, '%m/%d/%Y')
            to_date_obj_2 = datetime.datetime.strptime(to_date_2, '%m/%d/%Y')
            to_date_obj_2 = to_date_obj_2 + datetime.timedelta(hours=23, minutes=59, seconds=59)
            if from_date_obj_2 > to_date_obj_2:
                from_date_is_greater = True

            object_list = Quote.objects.filter(created_on__range=(from_date_obj_2, to_date_obj_2))
            for obj in object_list:
                quote_total_2 = quote_total_2 + estimate_total_calculator(obj.estimate.id)

            object_list = Order.objects.filter(created_on__range=(from_date_obj_2, to_date_obj_2))
            for obj in object_list:
                order_total_2 = order_total_2 + order_total_calculator(obj.proposal.estimate.id, obj)

            object_list = Invoice.objects.filter(created_on__range=(from_date_obj_2, to_date_obj_2))
            for obj in object_list:
                invoice_total_2 = invoice_total_2 + calculate_total_amount_due(obj)
                receive_total_2 = receive_total_2 + calculate_total_paid(obj)
                receivable_total_2 = receivable_total_2 + calculate_remaining_invoice_due(obj)

            if quote_total_1 != 0:
                quote_total_performance = (quote_total_2-quote_total_1)/quote_total_1 * 100
            if order_total_1 != 0:
                order_total_performance = (order_total_2-order_total_1)/order_total_1 * 100
            if invoice_total_1 != 0:
                invoice_total_performance = (invoice_total_2-invoice_total_1)/invoice_total_1 * 100
            if receive_total_1 != 0:
                receive_total_performance = (receive_total_2-receive_total_1)/receive_total_1 * 100
            if receivable_total_1 != 0:
                receivable_total_performance = (receivable_total_2-receivable_total_1)/receivable_total_1 * 100


    parameters = {
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'from_date_is_greater': from_date_is_greater,
        'from_date_obj_1': from_date_obj_1,
        'to_date_obj_1': to_date_obj_1,
        'quote_total_1': quote_total_1,
        'order_total_1': order_total_1,
        'invoice_total_1': invoice_total_1,
        'receive_total_1': receive_total_1,
        'receivable_total_1': receivable_total_1,
        'quote_total_2': quote_total_2,
        'order_total_2': order_total_2,
        'invoice_total_2': invoice_total_2,
        'receive_total_2': receive_total_2,
        'receivable_total_2': receivable_total_2,
        'quote_total_performance': quote_total_performance,
        'order_total_performance': order_total_performance,
        'invoice_total_performance': invoice_total_performance,
        'receive_total_performance': receive_total_performance,
        'receivable_total_performance': receivable_total_performance,
    }
    return render(request, "revenueList.html", parameters)
