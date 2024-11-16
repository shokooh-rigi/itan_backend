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

from .forms import *
from .render import Render as PDFRender
from django.conf import settings
from ..sheetcreator.models import *
from django.db.models import Count
from .models import DaltEquipment, DaltSheetData


# Create your views here.


@login_required
def dalt_sheet_list(request):
    search = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='dalt')
    object_list = object_list.filter(Q(project__proposal__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  }
    return render(request, "daltList.html", parameters)


@login_required
def dalt_sheet_add(request):
    form = DaltSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='dalt').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('daltSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='dalt')
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(name__iexact='dalt').exists():
                    equipment_type = Equipment.objects.get(name__iexact='dalt')
                for n in range(form.cleaned_data['equipment_quantity']):
                    flow_equipment = DaltEquipment(sheet=sheet, equipment_type=equipment_type)
                    flow_equipment.save()
                return redirect('daltSheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "daltSheetAdd.html", parameters)


@login_required
def dalt_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    dalt_equipments = DaltEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        dalt_equipments = dalt_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {'dalt_equipments': dalt_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': settings.WEB_URL,
                  'MEDIA_URL': settings.MEDIA_URL,
                  }
    return render(request, "daltSheetEquipmentsList.html", parameters)


@login_required
def dalt_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    equipment_type = Equipment.objects.get(name__iexact='dalt')
    dalt_equipment = DaltEquipment(sheet=my_sheet, equipment_type=equipment_type)
    dalt_equipment.save()
    return redirect('daltSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    dalt_equipments = DaltEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        dalt_equipments = dalt_equipments.filter(actual_data_entry_completed=True)
    dalt_equipment_data = []
    for dalt_equipment in dalt_equipments:
        dalt_equipment_obj = {}
        if is_report_pdf:
            daltsheetdatas = dalt_equipment.daltsheetdata_set.all()
        else:
            daltsheetdatas = dalt_equipment.daltsheetdata_set.filter(data_type=1)
        for dalt_data in daltsheetdatas:
            if dalt_data.sheet_field.field_name.lower() == 'duct area':
                duct_area = dalt_data.value
            elif dalt_data.sheet_field.field_name.lower() == 'leak factor':
                leak_factor = dalt_data.value
            dalt_equipment_obj[dalt_data.sheet_field.field_name + '-' + str(dalt_data.data_type)] = dalt_data.value
        if is_report_pdf:
            dalt_equipment_obj['mal'] = leak_factor
        dalt_equipment_data.append(dalt_equipment_obj)

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    stamp_signature = LicenseFiles.objects.get(key='ReportStamp').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    return {
        'my_sheet': my_sheet,
        'dalt_equipments': dalt_equipments,
        'dalt_equipment_data': dalt_equipment_data,
        'file_name': 'Dalt Sheet {}-{}{}'.format(my_sheet.project.proposal.estimate.project.name,
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
        'stamp_signature': stamp_signature,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/daltSheetPDFTemplate.html', parameters,
                                                  'daltPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/daltSheetPDFTemplate.html', parameters,
                                                  'daltPDFReport')

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
def dalt_design_data(request, dalt_equipment_id):
    dalt_equipment = get_object_or_404(DaltEquipment, id=dalt_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='dalt')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('daltSheetEquipmentList', dalt_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = DaltSheetData.objects.filter(data_type=1, dalt_equipment=dalt_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    DaltSheetData.objects.filter(data_type=1, dalt_equipment=dalt_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = DaltSheetData(data_type=1, dalt_equipment=dalt_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            dalt_equipment.design_data_entry_completed = True
            dalt_equipment.save()
            return redirect('daltSheetEquipmentList', dalt_equipment.sheet.id)

    parameters = {
        'dalt_equipment': dalt_equipment,
        'design_fields': design_fields,
    }
    return render(request, "daltSheetEquipmentDesignData.html", parameters)


@login_required
def dalt_actual_data(request, dalt_equipment_id):
    dalt_equipment = get_object_or_404(DaltEquipment, id=dalt_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='dalt')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('daltSheetEquipmentList', dalt_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:

                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = DaltSheetData.objects.filter(data_type=2, dalt_equipment=dalt_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    DaltSheetData.objects.filter(data_type=2, dalt_equipment=dalt_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = DaltSheetData(data_type=2, dalt_equipment=dalt_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            dalt_equipment.actual_data_entry_completed = True
            dalt_equipment.save()
            return redirect('daltSheetEquipmentList', dalt_equipment.sheet.id)

    parameters = {
        'dalt_equipment': dalt_equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "daltSheetEquipmentActualData.html", parameters)


@login_required
def dalt_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('daltSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('daltSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "daltSheetDelete.html", parameters)
