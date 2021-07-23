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
from .models import ChillerEquipment, ChillerSheetData


# Create your views here.


@login_required
def chiller_sheet_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='chiller')
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "chillerList.html", parameters)


@login_required
def chiller_sheet_add(request):
    form = ChillerSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='chiller').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('chillerSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='chiller')
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(name__iexact='chiller').exists():
                    equipment_type = Equipment.objects.get(name__iexact='chiller')
                for n in range(form.cleaned_data['equipment_quantity']):
                    chiller_equipment = ChillerEquipment(sheet=sheet, equipment_type=equipment_type)
                    chiller_equipment.save()
                return redirect('chillerSheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "chillerSheetAdd.html", parameters)


@login_required
def chiller_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    chiller_equipments = ChillerEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        chiller_equipments = chiller_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {'chiller_equipments': chiller_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "chillerSheetEquipmentsList.html", parameters)


@login_required
def chiller_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    equipment_type = Equipment.objects.get(name__iexact='CHILLER')
    chiller_equipment = ChillerEquipment(sheet=my_sheet, equipment_type=equipment_type)
    chiller_equipment.save()
    return redirect('chillerSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 2
    my_sheet = DataSheet.objects.get(id=sheet_id)
    chiller_equipments = ChillerEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        chiller_equipments = chiller_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(chiller_equipments.count() / total_pdf_row)
    chiller_equipment_data = []
    chiller_equipment_page = []
    i = 0
    for chiller_equipment in chiller_equipments:
        chiller_equipment_obj = {}
        chiller_equipment_obj['unit_number'] = chiller_equipment.unit_number
        chiller_equipment_obj['capacity'] = chiller_equipment.capacity
        chiller_equipment_obj['serial_number'] = chiller_equipment.serial_number
        if chiller_equipment.equipment:
            chiller_equipment_obj['manufacturer'] = chiller_equipment.equipment.manufacturer.name
            chiller_equipment_obj['model_number'] = chiller_equipment.equipment.model_number
        if is_report_pdf:
            chillersheetdatas = chiller_equipment.chillersheetdata_set.all()
        else:
            chillersheetdatas = chiller_equipment.chillersheetdata_set.filter(data_type=1)
        for chiller_data in chillersheetdatas:
            chiller_equipment_obj[chiller_data.sheet_field.field_name + '-' + str(chiller_data.data_type)] = chiller_data.value
        chiller_equipment_page.append(chiller_equipment_obj)
        i += 1
        if i == total_pdf_row:
            chiller_equipment_data.append(chiller_equipment_page)
            chiller_equipment_page = []
            i = 0
    if chiller_equipment_page:
        chiller_equipment_data.append(chiller_equipment_page)

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
        'empty_row_range': range(total_pdf_row - (chiller_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'chiller_equipments': chiller_equipments,
            'chiller_equipment_data': chiller_equipment_data
        },
        'file_name': 'Chiller Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/chillerSheetPDFTemplate.html', parameters,
                                                  'chillerPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/chillerSheetPDFTemplate.html', parameters,
                                                  'chillerPDFReport')

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
def chiller_common_data(request, chiller_equipment_id):
    chiller_equipment = get_object_or_404(ChillerEquipment, id=chiller_equipment_id)
    this_equipment = None
    if chiller_equipment.equipment:
        this_equipment = chiller_equipment.equipment
    form = ChillerSheetEquipmentForm(request.POST or None, request.FILES or None, instance=chiller_equipment)
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=chiller_equipment.equipment_type).distinct()
    equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='chiller', equipment_type=chiller_equipment.equipment_type)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['sheet'] = chiller_equipment.sheet
                saving_obj = form.save(commit=False)
                saving_obj.main_data_entry_completed = True
                if request.POST.get("id_equipment"):
                    selected_equipment = EquipmentDb.objects.get(id=request.POST.get("id_equipment"))
                    saving_obj.equipment = selected_equipment
                saving_obj.save()
                return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)

    parameters = {
        'form': form,
        'chiller_equipment': chiller_equipment,
        'manufacturers': manufacturers,
        'equipment_db': equipment_db,
        'this_equipment': this_equipment,
    }
    return render(request, "chillerSheetEquipmentGeneralData.html", parameters)


@login_required
def chiller_design_data(request, chiller_equipment_id):
    chiller_equipment = get_object_or_404(ChillerEquipment, id=chiller_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='chiller')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                if chiller_equipment.equipment:
                    if EquipmentDbDesignData.objects.filter(equipment=chiller_equipment.equipment.id, key=design_field.id).exists():
                        db_data = EquipmentDbDesignData.objects.get(equipment=chiller_equipment.equipment.id, key=design_field.id)
                        db_data.value = new_value
                        db_data.save()
                    else:
                        new_data = EquipmentDbDesignData(equipment=chiller_equipment.equipment.id, key=design_field.id, value=new_value)
                        new_data.save()

                num_results = ChillerSheetData.objects.filter(data_type=1, chiller_equipment=chiller_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    ChillerSheetData.objects.filter(data_type=1, chiller_equipment=chiller_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = ChillerSheetData(data_type=1, chiller_equipment=chiller_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            chiller_equipment.design_data_entry_completed = True
            chiller_equipment.save()
            return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)

    parameters = {
        'chiller_equipment': chiller_equipment,
        'design_fields': design_fields,
    }
    return render(request, "chillerSheetEquipmentDesignData.html", parameters)


@login_required
def chiller_actual_data(request, chiller_equipment_id):
    chiller_equipment = get_object_or_404(ChillerEquipment, id=chiller_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='chiller')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = ChillerSheetData.objects.filter(data_type=2, chiller_equipment=chiller_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    ChillerSheetData.objects.filter(data_type=2, chiller_equipment=chiller_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = ChillerSheetData(data_type=2, chiller_equipment=chiller_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            chiller_equipment.actual_data_entry_completed = True
            chiller_equipment.save()
            return redirect('chillerSheetEquipmentList', chiller_equipment.sheet.id)

    parameters = {
        'chiller_equipment': chiller_equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "chillerSheetEquipmentActualData.html", parameters)


@login_required
def chiller_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('chillerSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('chillerSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "chillerSheetDelete.html", parameters)
