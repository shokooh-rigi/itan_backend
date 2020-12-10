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
from .models import *
from .render import Render as PDFRender
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count


# Create your views here.


@login_required
def report_sheet_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-created_on'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = ReportSheet.objects.all()

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "reportSheetList.html", parameters)


@login_required
def report_sheet_add(request):
    form = ReportSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.all()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save()
                return redirect('reportSheetDrawing', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "reportSheetAdd.html", parameters)


@login_required
def report_sheet_drawing(request, sheet_id):
    form = ReportSheetDrawingForm(request.POST or None, request.FILES or None, initial={'report_sheet': sheet_id})
    drawings = ReportDrawing.objects.filter(report_sheet_id=sheet_id).order_by('created_on')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportSheetHome')
        if request.POST.get("reset"):
            for drawing in drawings:
                drawing.drawing_file.delete()
                drawing.delete()
            return redirect('reportSheetDrawing', sheet_id)
        if form.is_valid():
            if request.POST.get("add"):
                form.cleaned_data['report_sheet'] = sheet_id
                form.save()
                return redirect('reportSheetDrawing', sheet_id)
    parameters = {
        'form': form,
        'drawings': drawings,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "reportSheetDrawing.html", parameters)
