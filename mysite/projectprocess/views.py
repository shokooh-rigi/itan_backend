import math
import os
import re
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from ..estimator.views import estimate_total_calculator


# Create your views here.

def order_total_calculator(estimate_id, order):
    estimate_total = estimate_total_calculator(estimate_id)
    change_orders = ChangeOrder.objects.filter(order=order)
    co_total = 0
    for change_order in change_orders:
        co_total = co_total + change_order.amount
    order_total = float(estimate_total) + float(co_total)
    order_total = round(order_total, 2)
    return order_total


@login_required
def project_process_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-project_number'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__quote__estimate__project__name__icontains=search) |
                                       Q(project_number__icontains=search)).order_by(ordering)
    for obj in object_list:
        if order_total_calculator(obj.proposal.quote.estimate.id, obj) == 0:
            object_list = object_list.exclude(id=obj.id)


    if request.GET.get('type') == 'all' or request.GET.get('type') is None:
        object_list = object_list
    if request.GET.get('type') == 'tp':
        object_list = object_list.filter(projectprocess__tech_package=True)
    if request.GET.get('type') == 'ts':
        object_list = object_list.filter(projectprocess__tech_scheduled=True)
    if request.GET.get('type') == 'jc':
        object_list = object_list.filter(projectprocess__job_completed=True)
    if request.GET.get('type') == 'ro':
        object_list = object_list.filter(projectprocess__report_out=True)
    if request.GET.get('type') == 'in':
        object_list = object_list.filter(projectprocess__invoiced=True)
    if request.GET.get('type') == 'co':
        object_list = object_list.filter(projectprocess__completed=True)
    if request.GET.get('type') == 'ntp':
        object_list = object_list.filter(Q(projectprocess__tech_package=False) | Q(projectprocess__isnull=True))
    if request.GET.get('type') == 'nts':
        object_list = object_list.filter(Q(projectprocess__tech_scheduled=False) | Q(projectprocess__isnull=True))
    if request.GET.get('type') == 'njc':
        object_list = object_list.filter(Q(projectprocess__job_completed=False) | Q(projectprocess__isnull=True))
    if request.GET.get('type') == 'nro':
        object_list = object_list.filter(Q(projectprocess__report_out=False) | Q(projectprocess__isnull=True))
    if request.GET.get('type') == 'nin':
        object_list = object_list.filter(Q(projectprocess__invoiced=False) | Q(projectprocess__isnull=True))
    if request.GET.get('type') == 'nco':
        object_list = object_list.filter(Q(projectprocess__completed=False) | Q(projectprocess__isnull=True))

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    projects = paginator.get_page(page)


    parameters = {'projects': projects,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "projectProcessList.html", parameters)


@login_required
def project_process_edit(request, order_id, pre_demo):
    this_order = Order.objects.get(id=order_id)
    if pre_demo == 0:
        if ProjectProcess.objects.filter(order_id=order_id).exists():
            instance = get_object_or_404(ProjectProcess, order_id=order_id)
            form = ProjectProcessForm(request.POST or None, instance=instance)
        else:
            form = ProjectProcessForm(request.POST or None, initial={'order': order_id})
    else:
        if ProjectProcessPreDemo.objects.filter(order_id=order_id).exists():
            instance = get_object_or_404(ProjectProcessPreDemo, order_id=order_id)
            form = ProjectProcessPreDemoForm(request.POST or None, instance=instance)
        else:
            form = ProjectProcessPreDemoForm(request.POST or None, initial={'order': order_id})
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('projectProcessHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['order'] = order_id
                form.save()
                return redirect('projectProcessHome')
    parameters = {
        'form': form,
        'this_order': this_order,
    }
    return render(request, "projectProcessEdit.html", parameters)
