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
from .models import PrimaryHeatExchangerEquipment, PrimaryHeatExchangerSheetData


# Create your views here.
SHEET_TYPE_NAME = 'Primary Heat Exchanger'


@login_required
def primary_heat_exchanger_sheet_list(request):

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
        'generate_test_sheet_url': reverse('primaryHeatExchangerSheetAdd'),
        'equipment_add_url': '/primary-heat-exchanger/equipment_add/',
        'equipment_list_url': '/primary-heat-exchanger/equipments_list/',
        'sheet_delete_url': '/primary-heat-exchanger/delete/',
        'sheets': sheets,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "sheetList.html", parameters)


@login_required
def primary_heat_exchanger_sheet_add(request):
    form = PrimaryHeatExchangerSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME).values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('primaryHeatExchangerSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact=SHEET_TYPE_NAME)
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(test_sheet__name=SHEET_TYPE_NAME).count() > 0:
                    equipment_type = Equipment.objects.filter(test_sheet__name=SHEET_TYPE_NAME).first()
                for n in range(form.cleaned_data['equipment_quantity']):
                    primary_heat_exchanger_equipment = PrimaryHeatExchangerEquipment(sheet=sheet, equipment_type=equipment_type)
                    primary_heat_exchanger_equipment.save()
                return redirect('primaryHeatExchangerSheetEquipmentList', sheet.id)
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'form': form,
        'orders': orders,
    }
    return render(request, "sheetAdd.html", parameters)


@login_required
def primary_heat_exchanger_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    primary_heat_exchanger_equipments = PrimaryHeatExchangerEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        primary_heat_exchanger_equipments = primary_heat_exchanger_equipments.filter(Q(model_number__icontains=project_name)).distinct()
    parameters = {
        'equipments': primary_heat_exchanger_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': settings.WEB_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, "primaryHeatExchangerSheetEquipmentsList.html", parameters)


@login_required
def primary_heat_exchanger_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    primary_heat_exchanger_equipment = PrimaryHeatExchangerEquipment(sheet=my_sheet)
    primary_heat_exchanger_equipment.save()
    return redirect('primaryHeatExchangerSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 4
    my_sheet = DataSheet.objects.get(id=sheet_id)
    primary_heat_exchanger_equipments = PrimaryHeatExchangerEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        primary_heat_exchanger_equipments = primary_heat_exchanger_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(primary_heat_exchanger_equipments.count() / total_pdf_row)
    primary_heat_exchanger_equipment_data = []
    primary_heat_exchanger_equipment_page = []
    i = 0
    for primary_heat_exchanger_equipment in primary_heat_exchanger_equipments:
        primary_heat_exchanger_equipment_obj = {}
        primary_heat_exchanger_equipment_obj['location'] = primary_heat_exchanger_equipment.location
        primary_heat_exchanger_equipment_obj['service'] = primary_heat_exchanger_equipment.service
        primary_heat_exchanger_equipment_obj['rating_btu_hour'] = primary_heat_exchanger_equipment.rating_btu_hour
        primary_heat_exchanger_equipment_obj['serial_number'] = primary_heat_exchanger_equipment.serial_number
        primary_heat_exchanger_equipment_obj['unit_number'] = primary_heat_exchanger_equipment.unit_number
        if primary_heat_exchanger_equipment.equipment:
            primary_heat_exchanger_equipment_obj['manufacturer'] = primary_heat_exchanger_equipment.equipment.manufacturer.name
            primary_heat_exchanger_equipment_obj['model_number'] = primary_heat_exchanger_equipment.equipment.model_number
        if is_report_pdf:
            primary_heat_exchanger_sheetdatas = primary_heat_exchanger_equipment.primaryheatexchangersheetdata_set.all()
        else:
            primary_heat_exchanger_sheetdatas = primary_heat_exchanger_equipment.primaryheatexchangersheetdata_set.filter(data_type=1)
        for primary_heat_exchanger_data in primary_heat_exchanger_sheetdatas:
            primary_heat_exchanger_equipment_obj[primary_heat_exchanger_data.sheet_field.field_name + '-' + str(primary_heat_exchanger_data.data_type)] = primary_heat_exchanger_data.value
        primary_heat_exchanger_equipment_page.append(primary_heat_exchanger_equipment_obj)
        i += 1
        if i == total_pdf_row:
            primary_heat_exchanger_equipment_data.append(primary_heat_exchanger_equipment_page)
            primary_heat_exchanger_equipment_page = []
            i = 0
    if primary_heat_exchanger_equipment_page:
        primary_heat_exchanger_equipment_data.append(primary_heat_exchanger_equipment_page)

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
        'empty_row_range': range(total_pdf_row - (primary_heat_exchanger_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'equipments': primary_heat_exchanger_equipments,
            'equipment_data': primary_heat_exchanger_equipment_data
        },
        'file_name': 'Primary Heat Exchanger Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/primaryHeatExchangerSheetPDFTemplate.html', parameters,
                                                  'primaryHeatExchangerPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/primaryHeatExchangerSheetPDFTemplate.html', parameters,
                                                  'primaryHeatExchangerPDFReport')

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
def primary_heat_exchanger_common_data(request, primary_heat_exchanger_equipment_id):
    primary_heat_exchanger_equipment = get_object_or_404(PrimaryHeatExchangerEquipment, id=primary_heat_exchanger_equipment_id)
    this_equipment = None
    if primary_heat_exchanger_equipment.equipment:
        this_equipment = primary_heat_exchanger_equipment.equipment
    form = PrimaryHeatExchangerSheetEquipmentForm(request.POST or None, request.FILES or None, instance=primary_heat_exchanger_equipment)
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=primary_heat_exchanger_equipment.equipment_type).distinct()
    equipment_db = EquipmentDb.objects.filter(equipment_type=primary_heat_exchanger_equipment.equipment_type)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['sheet'] = primary_heat_exchanger_equipment.sheet
                saving_obj = form.save(commit=False)
                saving_obj.main_data_entry_completed = True
                if request.POST.get("id_equipment"):
                    selected_equipment = EquipmentDb.objects.get(id=request.POST.get("id_equipment"))
                    saving_obj.equipment = selected_equipment
                saving_obj.save()
                return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)

    parameters = {
        'form': form,
        'equipment': primary_heat_exchanger_equipment,
        'manufacturers': manufacturers,
        'equipment_db': equipment_db,
        'this_equipment': this_equipment,
    }
    return render(request, "primaryHeatExchangerSheetEquipmentGeneralData.html", parameters)


@login_required
def primary_heat_exchanger_design_data(request, primary_heat_exchanger_equipment_id):
    primary_heat_exchanger_equipment = get_object_or_404(PrimaryHeatExchangerEquipment, id=primary_heat_exchanger_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                if primary_heat_exchanger_equipment.equipment:
                    if EquipmentDbDesignData.objects.filter(equipment=primary_heat_exchanger_equipment.equipment.id, key=design_field.id).exists():
                        db_data = EquipmentDbDesignData.objects.get(equipment=primary_heat_exchanger_equipment.equipment.id, key=design_field.id)
                        db_data.value = new_value
                        db_data.save()
                    else:
                        new_data = EquipmentDbDesignData(equipment=primary_heat_exchanger_equipment.equipment.id, key=design_field.id, value=new_value)
                        new_data.save()

                num_results = PrimaryHeatExchangerSheetData.objects.filter(data_type=1, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    PrimaryHeatExchangerSheetData.objects.filter(data_type=1, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = PrimaryHeatExchangerSheetData(data_type=1, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            primary_heat_exchanger_equipment.design_data_entry_completed = True
            primary_heat_exchanger_equipment.save()
            return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)

    parameters = {
        'equipment': primary_heat_exchanger_equipment,
        'sheet_type_name': SHEET_TYPE_NAME,
        'design_fields': design_fields,
    }
    return render(request, "primaryHeatExchangerSheetEquipmentDesignData.html", parameters)


@login_required
def primary_heat_exchanger_actual_data(request, primary_heat_exchanger_equipment_id):
    primary_heat_exchanger_equipment = get_object_or_404(PrimaryHeatExchangerEquipment, id=primary_heat_exchanger_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = PrimaryHeatExchangerSheetData.objects.filter(data_type=2, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    PrimaryHeatExchangerSheetData.objects.filter(data_type=2, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = PrimaryHeatExchangerSheetData(data_type=2, primary_heat_exchanger_equipment=primary_heat_exchanger_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            primary_heat_exchanger_equipment.actual_data_entry_completed = True
            primary_heat_exchanger_equipment.save()
            return redirect('primaryHeatExchangerSheetEquipmentList', primary_heat_exchanger_equipment.sheet.id)

    parameters = {
        'equipment': primary_heat_exchanger_equipment,
        'sheet_type_name': SHEET_TYPE_NAME,
        'actual_fields': actual_fields,
    }
    return render(request, "primaryHeatExchangerSheetEquipmentActualData.html", parameters)


@login_required
def primary_heat_exchanger_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('primaryHeatExchangerSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('primaryHeatExchangerSheetHome')
    parameters = {
        'this_sheet': this_sheet,
        'sheet_type_name': SHEET_TYPE_NAME,
    }
    return render(request, "sheetDelete.html", parameters)
