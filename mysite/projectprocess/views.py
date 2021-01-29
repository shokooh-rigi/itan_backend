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


# Create your views here.


@login_required
def project_process_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = 'project_number'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Order.objects.filter(Q(proposal__quote__estimate__project__name__icontains=search) |
                                       Q(project_number__icontains=search)).order_by(ordering)

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

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    projects = paginator.get_page(page)


    parameters = {'projects': projects,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "projectProcessList.html", parameters)


@login_required
def project_process_edit(request, order_id):
    if ProjectProcess.objects.filter(order_id=order_id).exists():
        instance = get_object_or_404(ProjectProcess, order_id=order_id)
        form = ProjectProcessForm(request.POST or None, instance=instance)
    else:
        form = ProjectProcessForm(request.POST or None, initial={'order': order_id})
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('projectProcessHome')
        if form.is_valid():
            if request.POST.get("next"):
                form.cleaned_data['order'] = order_id
                form.save()
                return redirect('projectProcessHome')
    parameters = {'form': form,
                  }
    return render(request, "projectProcessEdit.html", parameters)
