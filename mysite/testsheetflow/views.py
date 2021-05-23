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
from .models import FlowEquipment, FlowSheetData


# Create your views here.


@login_required
def flow_sheet_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__icontains='flow')
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "flowList.html", parameters)


@login_required
def flow_sheet_add(request):
    form = FlowSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__icontains='flow').values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('flowSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='flow measuring')
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(name__iexact='FLOW METER FITTING MANUAL').exists():
                    equipment_type = Equipment.objects.get(name__iexact='FLOW METER FITTING MANUAL')
                for n in range(form.cleaned_data['equipment_quantity']):
                    flow_equipment = FlowEquipment(sheet=sheet, equipment_type=equipment_type)
                    flow_equipment.save()
                return redirect('flowSheetEquipmentList', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "flowSheetAdd.html", parameters)


@login_required
def flow_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    flow_equipments = FlowEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        flow_equipments = flow_equipments.filter(Q(unit_number__icontains=project_name) | Q(model_number__icontains=project_name)).distinct()
    parameters = {'flow_equipments': flow_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "flowSheetEquipmentsList.html", parameters)


@login_required
def flow_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    my_project = my_sheet.project
    vav_sheet_equipments = DataSheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='vav', sheet__project=my_project).filter(number_of_supply_air_terminal__gt=0)
    air_moving_sheet_equipments = SheetEquipment.objects.filter(sheet__test_sheet_type__name__icontains='air mov', sheet__project=my_project).filter(Q(number_of_supply_air_terminal__gt=0) | Q(number_of_return_air_terminal__gt=0) | Q(number_of_outside_air_terminal__gt=0) | Q(number_of_any_other__gt=0))
    vav_sheet_equipments = vav_sheet_equipments.filter(testsheetgeneraldata__value__icontains=project_name).order_by('terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed').distinct()
    air_moving_sheet_equipments = air_moving_sheet_equipments.filter(sheetequipmentcommondata__value__icontains=project_name).order_by('terminal_design_data_entry_completed', 'terminal_actual_data_entry_completed').distinct()
    parameters = {'air_moving_sheet_equipments': air_moving_sheet_equipments,
                  'vav_sheet_equipments': vav_sheet_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "velocitySheetEquipmentsList.html", parameters)


def fetch_sheet_equipment_data(this_sheet_equipment: AirTerminalEquipment, is_report_pdf: bool):
    if this_sheet_equipment.air_equipment:
        equipment_data = {
            'name': this_sheet_equipment.air_equipment.sheetequipmentcommondata_set.get(key__column_title__icontains='fan no.').value,
            'outlet_no': this_sheet_equipment.outlet_no,
            'code': this_sheet_equipment.code
        }
    else:
        equipment_data = {
            'name': this_sheet_equipment.vav_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value,
            'outlet_no': this_sheet_equipment.outlet_no,
            'code': this_sheet_equipment.code
        }

    design_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_design=True)
    design_data = [
        ('room_no', 'room no.'),
        ('size', 'size'),
        ('ak_factor', 'ak factor'),
        ('fpm', 'fpm'),
        ('cfm', 'cfm'),
    ]

    equipment_data['design'] = {}
    for key, val in design_data:
        design_field = design_fields.get(field_name__iexact=val)
        design_value = AirTerminalSheetData.objects.get(data_type=DataTypeChoices.Design.value, sheet_field=design_field,
                                                     air_terminal_equipment=this_sheet_equipment).value
        equipment_data['design'][key] = design_value

    if is_report_pdf:
        actual_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_actual=True)
        actual_data = [
            ('initial_fpm', 'initial fpm'),
            ('initial_cfm', 'initial cfm'),
            ('final_fpm', 'final fpm'),
            ('final_cfm', 'final cfm'),
            ('note', 'note'),
        ]
        equipment_data['actual'] = {}
        for key, val in actual_data:
            actual_field = actual_fields.get(field_name__iexact=val)
            actual_value = AirTerminalSheetData.objects.get(data_type=DataTypeChoices.Actual.value, sheet_field=actual_field,
                                                     air_terminal_equipment=this_sheet_equipment).value
            equipment_data['actual'][key] = actual_value

    return equipment_data


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 22
    my_sheet = DataSheet.objects.get(id=sheet_id)
    flow_equipments = FlowEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    total_pages = int(flow_equipments.count() / total_pdf_row) + 1
    flow_equipment_data = []
    for flow_equipment in flow_equipments:
        flow_equipment_obj = {}
        flow_equipment_obj['id'] = flow_equipment.id
        flow_equipment_obj['br_no'] = flow_equipment.br_number
        flow_equipment_obj['location'] = flow_equipment.location
        flow_equipment_obj['unit_number'] = flow_equipment.unit_number
        flow_equipment_obj['model_number'] = flow_equipment.model_number
        if is_report_pdf:
            flowsheetdatas = flow_equipment.flowsheetdata_set.all()
        else:
            flowsheetdatas = flow_equipment.flowsheetdata_set.filter(sheet_field__show_in_actual=False)
        for flow_data in flowsheetdatas:
            flow_equipment_obj[flow_data.sheet_field.field_name] = flow_data.value
        flow_equipment_data.append(flow_equipment_obj)

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
        'empty_row_range': range(total_pdf_row - (flow_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'my_sheet': my_sheet,
            'flow_equipments': flow_equipments,
            'flow_equipment_data': flow_equipment_data
        },
        'file_name': 'Flow Sheet {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/flowSheetPDFTemplate.html', parameters,
                                                  'flowPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/flowSheetPDFTemplate.html', parameters,
                                                  'flowPDFReport')

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
def flow_common_data(request, flow_equipment_id):
    flow_equipment = get_object_or_404(FlowEquipment, id=flow_equipment_id)
    form = FlowSheetEquipmentForm(request.POST or None, request.FILES or None, instance=flow_equipment)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['sheet'] = flow_equipment.sheet
                saving_obj = form.save(commit=False)
                saving_obj.main_data_entry_completed = True
                saving_obj.save()
                return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)

    parameters = {
        'form': form,
        'flow_equipment': flow_equipment,
    }
    return render(request, "flowSheetEquipmentGeneralData.html", parameters)


@login_required
def flow_design_data(request, flow_equipment_id):
    flow_equipment = get_object_or_404(FlowEquipment, id=flow_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains='flow')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                num_results = FlowSheetData.objects.filter(flow_equipment=flow_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    FlowSheetData.objects.filter(flow_equipment=flow_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = FlowSheetData(flow_equipment=flow_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            flow_equipment.design_data_entry_completed = True
            flow_equipment.save()
            return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)

    parameters = {
        'flow_equipment': flow_equipment,
        'design_fields': design_fields,
    }
    return render(request, "flowSheetEquipmentDesignData.html", parameters)


@login_required
def flow_actual_data(request, flow_equipment_id):
    flow_equipment = get_object_or_404(FlowEquipment, id=flow_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains='flow')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()

                num_results = FlowSheetData.objects.filter(flow_equipment=flow_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    FlowSheetData.objects.filter(flow_equipment=flow_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = FlowSheetData(flow_equipment=flow_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            flow_equipment.actual_data_entry_completed = True
            flow_equipment.save()
            return redirect('flowSheetEquipmentList', flow_equipment.sheet.id)

    parameters = {
        'flow_equipment': flow_equipment,
        'actual_fields': actual_fields,
    }
    return render(request, "flowSheetEquipmentActualData.html", parameters)


@login_required
def flow_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('flowSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('flowSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "flowSheetDelete.html", parameters)
