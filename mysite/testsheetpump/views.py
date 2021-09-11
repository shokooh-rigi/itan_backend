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
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from ..sheetcreator.models import *
from django.db.models import Count
from .models import PumpEquipment, PumpSheetData


# Create your views here.


@login_required
def pump_sheet_list(request):
    search = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='pump')
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "pumpList.html", parameters)


@login_required
def pump_sheet_add(request):
    form = PumpSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='pump').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pumpSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='pump')
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(name__iexact='PUMP').exists():
                    equipment_type = Equipment.objects.get(name__iexact='PUMP')
                for n in range(form.cleaned_data['equipment_quantity']):
                    pump_equipment = PumpEquipment(sheet=sheet, equipment_type=equipment_type)
                    pump_equipment.save()
                return redirect('pumpSheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "pumpSheetAdd.html", parameters)


@login_required
def pump_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    pump_equipments = PumpEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        pump_equipments = pump_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {'pump_equipments': pump_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "pumpSheetEquipmentsList.html", parameters)


@login_required
def pump_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    equipment_type = Equipment.objects.get(name__iexact='PUMP')
    pump_equipment = PumpEquipment(sheet=my_sheet, equipment_type=equipment_type)
    pump_equipment.save()
    return redirect('pumpSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 2
    my_sheet = DataSheet.objects.get(id=sheet_id)
    pump_equipments = PumpEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        pump_equipments = pump_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(pump_equipments.count() / total_pdf_row)
    pump_equipment_data = []
    pump_equipment_page = []
    i = 0
    for pump_equipment in pump_equipments:
        pump_equipment_obj = {}
        pump_equipment_obj['pump_number'] = pump_equipment.pump_number
        pump_equipment_obj['manufacturer'] = pump_equipment.manufacturer
        if is_report_pdf:
            pumpsheetdatas = pump_equipment.pumpsheetdata_set.all()
        else:
            pumpsheetdatas = pump_equipment.pumpsheetdata_set.filter(data_type=1)
        for pump_data in pumpsheetdatas:
            pump_equipment_obj[pump_data.sheet_field.field_name + '-' + str(pump_data.data_type)] = pump_data.value
        pump_equipment_page.append(pump_equipment_obj)
        i += 1
        if i == total_pdf_row:
            pump_equipment_data.append(pump_equipment_page)
            pump_equipment_page = []
            i = 0
    if pump_equipment_page:
        pump_equipment_data.append(pump_equipment_page)

    license_owner = LicenseInfo.objects.get(key='OwnerName').value
    owner_title = LicenseInfo.objects.get(key='OwnerTitle').value
    owner_tel = LicenseInfo.objects.get(key='OwnerTel').value
    owner_fax = LicenseInfo.objects.get(key='OwnerFax').value
    owner_web = LicenseInfo.objects.get(key='OwnerWeb').value
    owner_mail = LicenseInfo.objects.get(key='OwnerMail').value
    owner_signature = LicenseFiles.objects.get(key='OwnerSignature').value
    owner_logo = LicenseFiles.objects.get(key='OwnerLogo').value
    company_name = LicenseInfo.objects.get(key='CompanyName').value

    print(pump_equipment_data)

    return {
        'total_pdf_row': total_pdf_row,
        'empty_row_range': range(total_pdf_row - (pump_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'pump_equipments': pump_equipments,
            'pump_equipment_data': pump_equipment_data
        },
        'file_name': 'Pump Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/pumpSheetPDFTemplate.html', parameters,
                                                  'pumpPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/pumpSheetPDFTemplate.html', parameters,
                                                  'pumpPDFReport')

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
def pump_common_data(request, pump_equipment_id):
    pump_equipment = get_object_or_404(PumpEquipment, id=pump_equipment_id)
    this_equipment = None
    if pump_equipment.equipment:
        this_equipment = pump_equipment.equipment
    form = PumpSheetEquipmentForm(request.POST or None, request.FILES or None, instance=pump_equipment)
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=pump_equipment.equipment_type).distinct()
    equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='pump', equipment_type=pump_equipment.equipment_type)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['sheet'] = pump_equipment.sheet
                saving_obj = form.save(commit=False)
                saving_obj.main_data_entry_completed = True
                if request.POST.get("id_equipment"):
                    selected_equipment = EquipmentDb.objects.get(id=request.POST.get("id_equipment"))
                    saving_obj.equipment = selected_equipment
                saving_obj.save()
                return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)

    parameters = {
        'form': form,
        'pump_equipment': pump_equipment,
        'manufacturers': manufacturers,
        'equipment_db': equipment_db,
        'this_equipment': this_equipment,
    }
    return render(request, "pumpSheetEquipmentGeneralData.html", parameters)


@login_required
def pump_design_data(request, pump_equipment_id):
    pump_equipment = get_object_or_404(PumpEquipment, id=pump_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='pump')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = PumpSheetData.objects.filter(data_type=1, pump_equipment=pump_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    PumpSheetData.objects.filter(data_type=1, pump_equipment=pump_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = PumpSheetData(data_type=1, pump_equipment=pump_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            pump_equipment.design_data_entry_completed = True
            pump_equipment.save()
            return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)

    parameters = {
        'pump_equipment': pump_equipment,
        'design_fields': design_fields,
    }
    return render(request, "pumpSheetEquipmentDesignData.html", parameters)


@login_required
def pump_actual_data(request, pump_equipment_id):
    pump_equipment = get_object_or_404(PumpEquipment, id=pump_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='pump')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = PumpSheetData.objects.filter(data_type=2, pump_equipment=pump_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    PumpSheetData.objects.filter(data_type=2, pump_equipment=pump_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = PumpSheetData(data_type=2, pump_equipment=pump_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            pump_equipment.actual_data_entry_completed = True
            pump_equipment.save()
            return redirect('pumpSheetEquipmentList', pump_equipment.sheet.id)

    parameters = {
        'pump_equipment': pump_equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "pumpSheetEquipmentActualData.html", parameters)


@login_required
def pump_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('pumpSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('pumpSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "pumpSheetDelete.html", parameters)
