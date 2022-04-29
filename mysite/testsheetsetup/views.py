import re
from typing import Dict
import math
import os
from itertools import chain
from platform import system

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count


# Create your views here.

@login_required
def ts_setup_list(request):
    orders = Order.objects.exclude(id__in=Sheet.objects.filter(test_sheet_type_id=1).values_list('project_id')).order_by('-project_number')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetHome')
    parameters = {
        'orders': orders,
    }
    return render(request, "setupList.html", parameters)


@login_required
def ts_setup_edit(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetHome')

    parameters = {
        'order': order,
    }
    return render(request, "setupEdit.html", parameters)
