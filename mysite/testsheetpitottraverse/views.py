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
from .render import Render as PDFRender
from django.conf import settings
from ..sheetcreator.models import *
from django.db.models import Count
from .models import PitotTraverseSheetData


# Create your views here.
SHEET_TYPE_NAME = 'Pitot Traverse Summary'


@login_required
def pitot_traverse_summary_sheet_list(request):

    search = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME)
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'generate_test_sheet_url': reverse('pitotTraverseSummarySheetAdd'),
        'equipment_add_url': '/pitot_traverse_summary/equipment_add/',
        'equipment_list_url': '/pitot_traverse_summary/equipments_list/',
        'sheet_delete_url': '/pitot_traverse_summary/delete/',
        'sheets': sheets,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "sheetList.html", parameters)


@login_required
def pitot_traverse_summary_sheet_add(request):
    form = PitotTraverseSummarySheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME).values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pitotTraverseSummarySheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact=SHEET_TYPE_NAME)
                sheet.save()
                equipment_type = None
                for n in range(form.cleaned_data['equipment_quantity']):
                    pitot_traverse_summary_equipment = PitotTraverseEquipment(sheet=sheet, equipment_type=equipment_type)
                    pitot_traverse_summary_equipment.save()
                return redirect('pitotTraverseSummarySheetEquipmentList', sheet.id)
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'form': form,
        'orders': orders,
    }
    return render(request, "sheetAdd.html", parameters)


@login_required
def pitot_traverse_summary_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    pitot_traverse_summary_equipments = PitotTraverseEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        pitot_traverse_summary_equipments = pitot_traverse_summary_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipments': pitot_traverse_summary_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "pitotTraverseSummarySheetEquipmentsList.html", parameters)


@login_required
def pitot_traverse_summary_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    pitot_traverse_summary_equipment = PitotTraverseEquipment(sheet=my_sheet)
    pitot_traverse_summary_equipment.save()
    return redirect('pitotTraverseSummarySheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 22
    my_sheet = DataSheet.objects.get(id=sheet_id)
    pitot_traverse_summary_equipments = PitotTraverseEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        pitot_traverse_summary_equipments = pitot_traverse_summary_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(pitot_traverse_summary_equipments.count() / total_pdf_row)
    pitot_traverse_summary_equipment_data = []
    pitot_traverse_summary_equipment_page = []
    i = 0
    for pitot_traverse_summary_equipment in pitot_traverse_summary_equipments:
        pitot_traverse_summary_equipment_obj = {}
        if is_report_pdf:
            pitottraversesummarysheetdatas = pitot_traverse_summary_equipment.pitottraversesheetdata_set.all()
        else:
            pitottraversesummarysheetdatas = pitot_traverse_summary_equipment.pitottraversesheetdata_set.filter(data_type=1)
        for pitot_traverse_summary_data in pitottraversesummarysheetdatas:
            pitot_traverse_summary_equipment_obj[pitot_traverse_summary_data.sheet_field.field_name + '-' + str(pitot_traverse_summary_data.data_type)] = pitot_traverse_summary_data.value
        pitot_traverse_summary_equipment_page.append(pitot_traverse_summary_equipment_obj)
        i += 1
        if i == total_pdf_row:
            pitot_traverse_summary_equipment_data.append(pitot_traverse_summary_equipment_page)
            pitot_traverse_summary_equipment_page = []
            i = 0
    if pitot_traverse_summary_equipment_page:
        pitot_traverse_summary_equipment_data.append(pitot_traverse_summary_equipment_page)

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    return {
        'sheet_type_name': SHEET_TYPE_NAME,
        'total_pdf_row': total_pdf_row,
        'empty_row_range': range(total_pdf_row - (pitot_traverse_summary_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'equipments': pitot_traverse_summary_equipments,
            'equipment_data': pitot_traverse_summary_equipment_data
        },
        'file_name': SHEET_TYPE_NAME + ' Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
                                                     my_sheet.project.project_number,
                                                     '' if is_report_pdf else ' TECH').upper(),
        'license_owner': license_owner,
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
        'WEB_URL': settings.WEB_URL,
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
        'os': system(),
    }


@login_required
def equipments_generate_tech_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, False)
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/pitotTraverseSummarySheetPDFTemplate.html', parameters,
                                                  'pitotTraverseSummaryPDFReport')

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            my_file = fh.read()
            response = HttpResponse(my_file, content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            response['Content-Length'] = len(my_file)
            return response
    else:
        return 'error'


@login_required
def equipments_generate_report_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, True)
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/pitotTraverseSummarySheetPDFTemplate.html', parameters,
                                                  'pitotTraverseSummaryPDFReport')

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            my_file = fh.read()
            response = HttpResponse(my_file, content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            response['Content-Length'] = len(my_file)
            return response
    else:
        return 'error'


def split(value: str, sep: str):
    return value.replace(' ', '').split(sep)


def contains(value: str, sub: str):
    return value.find(sub) != -1


def manual_replace(s, char, index):
    return s[:index] + char + s[index +1:]


@login_required
def pitot_traverse_summary_design_data(request, equipment_id):
    equipment = get_object_or_404(PitotTraverseEquipment, id=equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pitotTraverseSummarySheetEquipmentList', equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = PitotTraverseSheetData.objects.filter(data_type=1, pitot_traverse_summary_equipment=equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    PitotTraverseSheetData.objects.filter(data_type=1, pitot_traverse_summary_equipment=equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = PitotTraverseSheetData(data_type=1, pitot_traverse_summary_equipment=equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            equipment.design_data_entry_completed = True
            equipment.save()
            return redirect('pitotTraverseSummarySheetEquipmentList', equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipment': equipment,
        'design_fields': design_fields,
    }
    return render(request, "pitotTraverseSummarySheetEquipmentDesignData.html", parameters)


@login_required
def pitot_traverse_summary_actual_data(request, equipment_id):
    equipment = get_object_or_404(PitotTraverseEquipment, id=equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pitotTraverseSummarySheetEquipmentList', equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = PitotTraverseSheetData.objects.filter(data_type=2, pitot_traverse_summary_equipment=equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    PitotTraverseSheetData.objects.filter(data_type=2, pitot_traverse_summary_equipment=equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = PitotTraverseSheetData(data_type=2, pitot_traverse_summary_equipment=equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            equipment.actual_data_entry_completed = True
            equipment.save()
            return redirect('pitotTraverseSummarySheetEquipmentList', equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipment': equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "pitotTraverseSummarySheetEquipmentActualData.html", parameters)


@login_required
def pitot_traverse_summary_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pitotTraverseSummarySheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('pitotTraverseSummarySheetHome')
    parameters = {
        'this_sheet': this_sheet,
        'sheet_type_name': SHEET_TYPE_NAME,
    }
    return render(request, "sheetDelete.html", parameters)
