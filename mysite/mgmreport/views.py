from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render

from mysite.estimator.models import *
from mysite.estimator.views import estimate_total_calculator
from mysite.gi.models import Invoice
from mysite.order.models import Order
from django.conf import settings


@login_required
def equipments_list(request):
    equipments = Equipment.objects.all().order_by('service', 'name')

    # Archive company

    # if request.method == 'POST':
    #     delete_request = request.POST[0]
    #     deleting_record = delete_request[3:]

    parameters = {'equipments': equipments,
                  }
    return render(request, "equipmentslist.html", parameters)


@login_required
def company_list(request):
    contacts = Person.objects.order_by('company__company_type', 'company')

    parameters = {
        'contacts': contacts
    }
    return render(request, "companylist.html", parameters)


@login_required
def bids_list(request, bid_type):
    object_list = ''

    from_date = request.GET.get("fromDate")
    to_date = request.GET.get("toDate")

    from_date_is_greater = False

    if from_date and to_date:
        if bid_type == 'estimate':
            object_list = Estimate.objects.all().order_by('customer')
        if bid_type == 'quote':
            object_list = Quote.objects.all().order_by('estimate__customer')
        if bid_type == 'proposal':
            object_list = Proposal.objects.all().order_by('estimate__customer')
        if bid_type == 'order':
            object_list = Order.objects.all().order_by('proposal__estimate__customer')
        if bid_type == 'invoice':
            object_list = Invoice.objects.all().order_by('order__proposal__estimate__customer')
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')
        to_date_obj = to_date_obj + datetime.timedelta(hours=23, minutes=59, seconds=59)
        if from_date_obj > to_date_obj:
            from_date_is_greater = True
        if bid_type == 'estimate':
            object_list = object_list.filter(due_date__range=(from_date_obj, to_date_obj))
        if bid_type == 'quote':
            object_list = object_list.filter(created_on__range=(from_date_obj, to_date_obj))
        if bid_type == 'proposal':
            object_list = object_list.filter(created_on__range=(from_date_obj, to_date_obj))
        if bid_type == 'order':
            object_list = object_list.filter(created_on__range=(from_date_obj, to_date_obj))
        if bid_type == 'invoice':
            object_list = object_list.filter(created_on__range=(from_date_obj, to_date_obj))

    customer_rows = {}
    total_of_all = 0
    total_rows = 0
    for row in object_list:
        rowfromestimate = row
        if bid_type == 'quote':
            rowfromestimate = row.estimate
        if bid_type == 'proposal':
            rowfromestimate = row.quote.estimate
        if bid_type == 'order':
            rowfromestimate = row.proposal.estimate
        if bid_type == 'invoice':
            rowfromestimate = row.order.proposal.estimate
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
    parameters = {
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'customer_rows': customer_rows,
        'total_of_all': total_of_all,
        'total_rows': total_rows,
        'from_date_is_greater': from_date_is_greater,
        'bid_type': bid_type
    }
    return render(request, "bidslist.html", parameters)


@login_required
def detailed_orders_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__estimate__project__name__icontains=project_name) |
                                       Q(project_number__icontains=project_name) |
                                       Q(proposal__estimate__customer__company__name__icontains=project_name)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    parameters = {'orders': orders,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  }
    return render(request, "detailedorder.html", parameters)