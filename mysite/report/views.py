import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from mysite.order.models import Order
from .forms import ReportForm
from .models import Report
from ..settings import MEDIA_URL, WEB_URL


# Create your views here.


@login_required
def report_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    from_date = request.GET.get("fromDate", '01/01/2000')
    to_date = request.GET.get("toDate", '01/01/2100')
    if from_date and to_date:
        from_date_obj = datetime.datetime.strptime(from_date, '%m/%d/%Y')
        to_date_obj = datetime.datetime.strptime(to_date, '%m/%d/%Y')
        to_date_obj = to_date_obj + datetime.timedelta(hours=23, minutes=59, seconds=59)

        object_list = Report.objects.filter(Q(order__proposal__quote__estimate__project__name__icontains=search)
                                            | Q(order__project_number__icontains=search)) \
            .filter(created_on__range=(from_date_obj, to_date_obj)).order_by(ordering)

    else:
        object_list = Report.objects.filter(Q(order__proposal__quote__estimate__project__name__icontains=search)
                                            | Q(order__project_number__icontains=search)) \
            .order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    reports = paginator.get_page(page)

    parameters = {'reports': reports,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "report.html", parameters)


@login_required
def report_add(request):
    form = ReportForm(request.POST or None, request.FILES or None, initial={'created_by': request.user})
    orders = Order.objects.filter(archive=False).exclude(id__in=Report.objects.all().values_list('order_id')) \
        .order_by('-created_on')
    if request.method == 'POST':
        form.fields['created_by'].widget = forms.HiddenInput()
        if request.POST.get("cancel"):
            return redirect('reportHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['created_by'] = request.user
                form.save()
                return redirect('reportHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "reportAdd.html", parameters)


@login_required
def report_edit(request, report_id):
    this_report = get_object_or_404(Report, id=report_id)
    form = ReportForm(request.POST or None, request.FILES or None, instance=this_report)
    orders = Order.objects.filter(archive=False).exclude(id__in=Report.objects.all().values_list('order_id')) \
        .order_by('-created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportHome')
        if form.is_valid():
            if request.POST.get("save"):
                form.save()
                return redirect('reportHome')
    parameters = {'form': form,
                  'orders': orders
                  }
    return render(request, "reportEdit.html", parameters)


@login_required
def report_delete(request, report_id):
    this_report = get_object_or_404(Report, id=report_id)
    if request.method == "POST" and request.user.is_authenticated and this_report.order.proposal.quote.estimate.created_by == request.user:
        if request.POST.get("confirm"):
            this_report.delete()
        return redirect('reportHome')
    elif request.method == "POST" and request.user.is_authenticated and this_report.order.proposal.quote.estimate.created_by != request.user:
        if request.POST.get("confirm"):
            error_msg = "This record was created by another user, you are not authorized to delete this record."
            parameters = {
                'this_report': this_report,
                'error_msg': error_msg
            }
            return render(request, "reportDelete.html", parameters)
        return redirect('invoiceHome')
    parameters = {'this_report': this_report
                  }
    return render(request, "reportDelete.html", parameters)
