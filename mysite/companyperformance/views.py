from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from mysite.core.models import ContactInfo
from mysite.estimator.models import *
from mysite.estimator.views import estimate_total_calculator
from mysite.order.models import Order
from django.conf import settings

from mysite.proposal.models import Proposal
from ..scheduler.models import Schedule, Maintenance
from django.db.models import Q


def is_num(data):
    try:
        int(data)
        return True
    except ValueError:
        return False


@login_required
def performance_list(request):
    object_list = ''

    search = request.GET.get('search', '')

    from_date = request.GET.get("fromDate")
    to_date = request.GET.get("toDate")
    from_date_obj = ''
    to_date_obj = ''

    from_date_is_greater = False
    if from_date and to_date:
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')
        to_date_obj = to_date_obj + datetime.timedelta(hours=23, minutes=59, seconds=59)
        if from_date_obj > to_date_obj:
            from_date_is_greater = True

        object_list = ContactInfo.objects.order_by('customer_id').filter(name__icontains=search)
        if is_num(search):
            object_list = ContactInfo.objects.order_by('customer_id').filter(Q(customer_id=search) | Q(name=search))
        for this_object in object_list:
            if Proposal.objects.filter(estimate__customer__company=this_object, created_on__range=(from_date_obj, to_date_obj)).count() == 0:
                object_list = object_list.exclude(id=this_object.id)
    parameters = {
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'object_list': object_list,
        'from_date_is_greater': from_date_is_greater,
        'from_date_obj': from_date_obj,
        'to_date_obj': to_date_obj
    }
    return render(request, "companyPerformanceList.html", parameters)
