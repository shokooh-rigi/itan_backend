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
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count
from .models import VbtsEquipment, VbtsSheetData


# Create your views here.
SHEET_TYPE_NAME = 'V.A.V. Box Temperature Schedule'

@login_required
def sheet_list(request):
    search = request.GET.get('search', '')

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
        'generate_test_sheet_url': reverse('vbtsSheetAdd'),
        'equipment_add_url': '/vbts/equipment_add/',
        'equipment_list_url': '/vbts/equipments_list/',
        'sheet_delete_url': '/vbts/delete/',
        'sheets': sheets,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "sheetList.html", parameters)


@login_required
def sheet_add(request):
    form = VbtsSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME).values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vbtsSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact=SHEET_TYPE_NAME)
                sheet.save()
                equipment_type = None
                for n in range(form.cleaned_data['equipment_quantity']):
                    vbts_equipment = VbtsEquipment(sheet=sheet, equipment_type=equipment_type)
                    vbts_equipment.save()
                return redirect('vbtsSheetEquipmentList', sheet.id)
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'form': form,
        'orders': orders,
    }
    return render(request, "sheetAdd.html", parameters)


@login_required
def sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    vbts_equipments = VbtsEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        vbts_equipments = vbts_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipments': vbts_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "vbtsSheetEquipmentsList.html", parameters)


@login_required
def equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    vbts_equipment = VbtsEquipment(sheet=my_sheet)
    vbts_equipment.save()
    return redirect('vbtsSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 22
    my_sheet = DataSheet.objects.get(id=sheet_id)
    vbts_equipments = VbtsEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        vbts_equipments = vbts_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(vbts_equipments.count() / total_pdf_row)
    vbts_equipment_data = []
    vbts_equipment_page = []
    i = 0
    for vbts_equipment in vbts_equipments:
        vbts_equipment_obj = {}
        if is_report_pdf:
            vbtssheetdatas = vbts_equipment.vbtssheetdata_set.all()
        else:
            vbtssheetdatas = vbts_equipment.vbtssheetdata_set.filter(data_type=1)
        for vbts_data in vbtssheetdatas:
            vbts_equipment_obj[vbts_data.sheet_field.field_name + '-' + str(vbts_data.data_type)] = vbts_data.value
        vbts_equipment_page.append(vbts_equipment_obj)
        i += 1
        if i == total_pdf_row:
            vbts_equipment_data.append(vbts_equipment_page)
            vbts_equipment_page = []
            i = 0
    if vbts_equipment_page:
        vbts_equipment_data.append(vbts_equipment_page)

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    print(vbts_equipment_data)

    return {
        'total_pdf_row': total_pdf_row,
        'empty_row_range': range(total_pdf_row - (vbts_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'vbts_equipments': vbts_equipments,
            'vbts_equipment_data': vbts_equipment_data
        },
        'sheet_type_name': SHEET_TYPE_NAME,
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
        'WEB_URL': WEB_URL,
        'STATIC_URL': STATIC_URL,
        'MEDIA_URL': MEDIA_URL,
        'os': system(),
    }


@login_required
def equipments_generate_tech_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, False)
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/vbtsSheetPDFTemplate.html', parameters,
                                                  'vbtsPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/vbtsSheetPDFTemplate.html', parameters,
                                                  'vbtsPDFReport')

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
def design_data(request, equipment_id):
    vbts_equipment = get_object_or_404(VbtsEquipment, id=equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vbtsSheetEquipmentList', vbts_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = VbtsSheetData.objects.filter(data_type=1, vbts_equipment=vbts_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    VbtsSheetData.objects.filter(data_type=1, vbts_equipment=vbts_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = VbtsSheetData(data_type=1, vbts_equipment=vbts_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            vbts_equipment.design_data_entry_completed = True
            vbts_equipment.save()
            return redirect('vbtsSheetEquipmentList', vbts_equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'vbts_equipment': vbts_equipment,
        'design_fields': design_fields,
    }
    return render(request, "vbtsSheetEquipmentDesignData.html", parameters)


@login_required
def actual_data(request, equipment_id):
    vbts_equipment = get_object_or_404(VbtsEquipment, id=equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__iexact=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vbtsSheetEquipmentList', vbts_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = VbtsSheetData.objects.filter(data_type=2, vbts_equipment=vbts_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    VbtsSheetData.objects.filter(data_type=2, vbts_equipment=vbts_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = VbtsSheetData(data_type=2, vbts_equipment=vbts_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            vbts_equipment.actual_data_entry_completed = True
            vbts_equipment.save()
            return redirect('vbtsSheetEquipmentList', vbts_equipment.sheet.id)

    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'vbts_equipment': vbts_equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "vbtsSheetEquipmentActualData.html", parameters)


@login_required
def sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vbtsSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('vbtsSheetHome')
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'this_sheet': this_sheet,
    }
    return render(request, "vbtsSheetDelete.html", parameters)
