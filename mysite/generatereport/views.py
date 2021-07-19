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
from ..sheetcreator.views import equipments_generate_report_pdf as generate_air_moving_sheet
from ..testsheetvav.views import equipments_generate_report_pdf as generate_air_moving_sheet
from PyPDF2 import PdfFileMerger
import random
from ..settings import MEDIA_URL_NOSLASH
import img2pdf
from PIL import Image


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
    orders = Order.objects.exclude(id__in=ReportSheet.objects.values_list('project_id')).order_by('project_number')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('reportSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                report_sheet = form.save()
                return redirect('reportSheetHome')
    parameters = {
        'form': form,
        'orders': orders,
    }
    return render(request, "reportSheetAdd.html", parameters)


@login_required
def report_sheet_recreate(request, sheet_id):
    report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    report_stamp = LicenseFiles.objects.get(key='ReportStamp').value
    instruction_image = LicenseFiles.objects.get(key='InstructionReport').value
    abbreviation_image = LicenseFiles.objects.get(key='AbbreviationReport').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    parameters = {
        'file_name': ('COVER SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper(),
        'report_sheet': report_sheet,
        'report_stamp': report_stamp,
        'datetime': datetime.datetime.now(),
        'license_owner': license_owner,
        'instruction_image': instruction_image,
        'abbreviation_image': abbreviation_image,
        'owner_title': owner_title,
        'owner_address_line1': LicenseInfo.objects.get(key='OwnerAddressLine1').value,
        'owner_address_line2': LicenseInfo.objects.get(key='OwnerAddressLine2').value,
        'owner_tel': owner_tel,
        'owner_fax': owner_fax,
        'owner_web': owner_web,
        'owner_mail': owner_mail,
        'owner_signature': owner_signature,
        'owner_logo': owner_logo,
        'pdf_header_logo': LicenseFiles.objects.get(key='PDFHeaderLogo').value,
        'pdf_header_text': LicenseInfo.objects.get(key='PDFHeaderText').value,
        'company_name': company_name,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
        'STATIC_URL': STATIC_URL,
        'os': system()
    }

    cover_pdf = ReportSheet.create_cover_pdf(parameters)
    parameters['cover_pdf'] = cover_pdf[1]

    parameters['file_name'] = ('REPORT SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name,
                                                           report_sheet.project.project_number)).upper()
    report_pdf = ReportSheet.create_report_pdf(parameters)
    parameters['report_pdf'] = report_pdf[1]

    merger = PdfFileMerger()
    cover = open(cover_pdf[1], "rb")
    merger.append(fileobj=cover)

    table_of_content_file = open(MEDIA_URL_NOSLASH + report_sheet.upload_table_of_content.name, "rb")
    merger.append(fileobj=table_of_content_file)

    report = open(report_pdf[1], "rb")
    merger.append(fileobj=report)

    test_sheets = open(MEDIA_URL_NOSLASH + report_sheet.upload_test_sheets.name, "rb")
    merger.append(fileobj=test_sheets)

    drawings = open(MEDIA_URL_NOSLASH + report_sheet.upload_drawing_pdf.name, "rb")
    merger.append(fileobj=drawings)

    if not os.path.exists(
            os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report")):
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname("__file__")), "media/pdfs/report"))
    output = open(MEDIA_URL_NOSLASH + "pdfs/report/" + ('FINAL SHEET {}-{}'.format(report_sheet.project.proposal.quote.estimate.project.name, report_sheet.project.project_number)).upper() + ".pdf", "wb")
    merger.write(output)
    cover.close()
    table_of_content_file.close()
    test_sheets.close()
    drawings.close()

    return redirect('reportSheetHome')


@login_required
def report_sheet_finalize(request, sheet_id):
    report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    report_sheet.project.projectprocess.tech_package = True
    report_sheet.project.projectprocess.tech_scheduled = True
    report_sheet.project.projectprocess.job_completed = True
    report_sheet.project.projectprocess.report_out = True
    report_sheet.project.projectprocess.report_out_date = datetime.datetime.now().date()
    report_sheet.project.projectprocess.save()
    report_sheet.project.completion_percentage = 100
    report_sheet.project.pre_demo_completion_percentage = 100
    report_sheet.project.save()
    return redirect('reportSheetHome')

# @login_required
# def report_sheet_drawing(request, sheet_id):
#     form = ReportSheetDrawingForm(request.POST or None, request.FILES or None, initial={'report_sheet': sheet_id})
#     drawings = ReportDrawing.objects.filter(report_sheet_id=sheet_id).order_by('created_on')
#     if request.method == 'POST':
#         if request.POST.get("cancel"):
#             return redirect('reportSheetHome')
#         if request.POST.get("reset"):
#             for drawing in drawings:
#                 drawing.drawing_file.delete()
#                 drawing.delete()
#             return redirect('reportSheetDrawing', sheet_id)
#         if form.is_valid():
#             if request.POST.get("add"):
#                 form.cleaned_data['report_sheet'] = sheet_id
#                 form.save()
#                 return redirect('reportSheetDrawing', sheet_id)
#     parameters = {
#         'form': form,
#         'drawings': drawings,
#         'WEB_URL': WEB_URL,
#         'MEDIA_URL': MEDIA_URL,
#     }
#     return render(request, "reportSheetDrawing.html", parameters)


@login_required
def delete_report_sheet(request, sheet_id):
    this_report_sheet = get_object_or_404(ReportSheet, id=sheet_id)
    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("confirm"):
            this_report_sheet.upload_drawing_pdf.delete()
            parameters = {
                'file_name': ('REPORT SHEET {}-{}'.format(this_report_sheet.project.proposal.quote.estimate.project.name,
                                                          this_report_sheet.project.project_number)).upper(),
            }
            ReportSheet.delete_report_pdf(parameters)
            this_report_sheet.delete()
        return redirect('reportSheetHome')
    parameters = {'this_report_sheet': this_report_sheet
                  }
    return render(request, "reportSheetDelete.html", parameters)

