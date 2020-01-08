from .forms import *
from django.shortcuts import render
from django.views.generic import ListView
from mysite.estimator.models import *
from mysite.order.models import Order
from mysite.gi.models import Invoice
import datetime
from django.core.paginator import Paginator
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from mysite.estimator.views import estimate_total_calculator
from django.contrib.auth.decorators import login_required


@login_required
def equipments_list(request):
    equipments = Equipment.objects.all().order_by('service', 'name')

    parameters = {'equipments': equipments,
                  }
    return render(request, "equipmentslist.html", parameters)


@login_required
def company_list(request):
    contacts = Person.objects.order_by('company__company_type', 'company')

    parameters = {'contacts': contacts
                  }
    return render(request, "companylist.html", parameters)


@login_required
def bids_list(request):

    object_list = Estimate.objects.all().order_by('customer')
    if request.GET.get('type') == 'quote':
        object_list = Quote.objects.all().order_by('estimate__customer')
    if request.GET.get('type') == 'proposal':
        object_list = Proposal.objects.all().order_by('quote__estimate__customer')
    if request.GET.get('type') == 'order':
        object_list = Order.objects.all().order_by('proposal__quote__estimate__customer')
    if request.GET.get('type') == 'invoice':
        object_list = Invoice.objects.all().order_by('order__proposal__quote__estimate__customer')

    from_date = request.GET.get("fromDate", '01/01/2000')
    to_date = request.GET.get("toDate", '01/01/2100')

    if from_date and to_date:
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')
        if request.GET.get('type') == 'estimate' or request.GET.get('type') == '':
            object_list = object_list.filter(due_date__range=(from_date_obj, to_date_obj))
        if request.GET.get('type') == 'quote':
            object_list = object_list.filter(estimate__due_date__range=(from_date_obj, to_date_obj))
        if request.GET.get('type') == 'proposal':
            object_list = object_list.filter(quote__estimate__due_date__range=(from_date_obj, to_date_obj))
        if request.GET.get('type') == 'order':
            object_list = object_list.filter(estimated_date_of_project__range=(from_date_obj, to_date_obj))
        if request.GET.get('type') == 'invoice':
            object_list = object_list.filter(created_on__range=(from_date_obj, to_date_obj))

    customer_rows = {}
    total_of_all = 0
    total_rows = 0
    for row in object_list:
        rowfromestimate = row
        if request.GET.get('type') == 'quote':
            rowfromestimate = row.estimate
        if request.GET.get('type') == 'proposal':
            rowfromestimate = row.quote.estimate
        if request.GET.get('type') == 'order':
            rowfromestimate = row.proposal.quote.estimate
        if request.GET.get('type') == 'invoice':
            rowfromestimate = row.order.proposal.quote.estimate
        if rowfromestimate.customer.id not in customer_rows:
            customer_rows[rowfromestimate.customer.id] = {
                "customer_name": rowfromestimate.customer,
                "total_bids": 0,
                "total": 0
            }
        customer_rows[rowfromestimate.customer.id]["total_bids"] += 1
        customer_rows[rowfromestimate.customer.id]["total"] += estimate_total_calculator(rowfromestimate.id)
        total_rows += 1
        total_of_all += estimate_total_calculator(rowfromestimate.id)
    parameters = {'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  'customer_rows': customer_rows,
                  'total_of_all': total_of_all,
                  'total_rows': total_rows,
                  }
    return render(request, "bidslist.html", parameters)
