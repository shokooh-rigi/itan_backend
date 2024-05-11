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
from .models import InductionUnitEquipment, InductionUnitSheetData


# Create your views here.
SHEET_TYPE_NAME = 'Induction Unit'


@login_required
def induction_unit_sheet_list(request):

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
        'generate_test_sheet_url': reverse('inductionUnitSheetAdd'),
        'equipment_add_url': '/induction_unit/equipment_add/',
        'equipment_list_url': '/induction_unit/equipments_list/',
        'sheet_delete_url': '/induction_unit/delete/',
        'sheets': sheets,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "sheetList.html", parameters)


@login_required
def induction_unit_sheet_add(request):
    form = InductionUnitSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME).values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('inductionUnitSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact=SHEET_TYPE_NAME)
                sheet.save()
                equipment_type = None
                for n in range(form.cleaned_data['equipment_quantity']):
                    induction_unit_equipment = InductionUnitEquipment(sheet=sheet, equipment_type=equipment_type)
                    induction_unit_equipment.save()
                return redirect('inductionUnitSheetEquipmentList', sheet.id)
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'form': form,
        'orders': orders,
    }
    return render(request, "sheetAdd.html", parameters)


@login_required
def induction_unit_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    induction_unit_equipments = InductionUnitEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        induction_unit_equipments = induction_unit_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipments': induction_unit_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "inductionUnitSheetEquipmentsList.html", parameters)


@login_required
def induction_unit_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    induction_unit_equipment = InductionUnitEquipment(sheet=my_sheet)
    induction_unit_equipment.save()
    return redirect('inductionUnitSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 22
    my_sheet = DataSheet.objects.get(id=sheet_id)
    induction_unit_equipments = InductionUnitEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        induction_unit_equipments = induction_unit_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(induction_unit_equipments.count() / total_pdf_row)
    induction_unit_equipment_data = []
    induction_unit_equipment_page = []
    i = 0
    for induction_unit_equipment in induction_unit_equipments:
        induction_unit_equipment_obj = {}
        if is_report_pdf:
            inductionunitsheetdatas = induction_unit_equipment.inductionunitsheetdata_set.all()
        else:
            inductionunitsheetdatas = induction_unit_equipment.inductionunitsheetdata_set.filter(data_type=1)
        for induction_unit_data in inductionunitsheetdatas:
            induction_unit_equipment_obj[induction_unit_data.sheet_field.field_name + '-' + str(induction_unit_data.data_type)] = induction_unit_data.value
        induction_unit_equipment_page.append(induction_unit_equipment_obj)
        i += 1
        if i == total_pdf_row:
            induction_unit_equipment_data.append(induction_unit_equipment_page)
            induction_unit_equipment_page = []
            i = 0
    if induction_unit_equipment_page:
        induction_unit_equipment_data.append(induction_unit_equipment_page)

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
        'total_pdf_row': total_pdf_row,
        'empty_row_range': range(total_pdf_row - (induction_unit_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'induction_unit_equipments': induction_unit_equipments,
            'induction_unit_equipment_data': induction_unit_equipment_data
        },
        'file_name': 'VAV Box Fan Heat Schedule Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/inductionUnitSheetPDFTemplate.html', parameters,
                                                  'inductionUnitPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/inductionUnitSheetPDFTemplate.html', parameters,
                                                  'inductionUnitPDFReport')

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
def induction_unit_design_data(request, induction_unit_equipment_id):
    equipment = get_object_or_404(InductionUnitEquipment, id=induction_unit_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('inductionUnitSheetEquipmentList', equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = InductionUnitSheetData.objects.filter(data_type=1, induction_unit_equipment=equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    InductionUnitSheetData.objects.filter(data_type=1, induction_unit_equipment=equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = InductionUnitSheetData(data_type=1, induction_unit_equipment=equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            equipment.design_data_entry_completed = True
            equipment.save()
            return redirect('inductionUnitSheetEquipmentList', equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipment': equipment,
        'design_fields': design_fields,
    }
    return render(request, "inductionUnitSheetEquipmentDesignData.html", parameters)


@login_required
def induction_unit_actual_data(request, induction_unit_equipment_id):
    equipment = get_object_or_404(InductionUnitEquipment, id=induction_unit_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('inductionUnitSheetEquipmentList', equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = InductionUnitSheetData.objects.filter(data_type=2, induction_unit_equipment=equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    InductionUnitSheetData.objects.filter(data_type=2, induction_unit_equipment=equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = InductionUnitSheetData(data_type=2, induction_unit_equipment=equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            equipment.actual_data_entry_completed = True
            equipment.save()
            return redirect('inductionUnitSheetEquipmentList', equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipment': equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "inductionUnitSheetEquipmentActualData.html", parameters)


@login_required
def induction_unit_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('inductionUnitSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('inductionUnitSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "inductionUnitSheetDelete.html", parameters)
