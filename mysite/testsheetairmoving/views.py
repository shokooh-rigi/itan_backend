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
from .models import AirMovingEquipment, AirMovingSheetData


# Create your views here.
SHEET_TYPE_NAME = 'Air Moving Equipment'


@login_required
def air_moving_equipment_sheet_list(request):

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
        'generate_test_sheet_url': reverse('airMovingEquipmentSheetAdd'),
        'equipment_add_url': '/air-moving-equipment/equipment_add/',
        'equipment_list_url': '/air-moving-equipment/equipments_list/',
        'sheet_delete_url': '/air-moving-equipment/delete/',
        'sheets': sheets,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "sheetList.html", parameters)


@login_required
def air_moving_equipment_sheet_add(request):
    form = AirMovingEquipmentSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact=SHEET_TYPE_NAME).values_list('project_id')).order_by('-project_number').distinct()
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('airMovingEquipmentSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact=SHEET_TYPE_NAME)
                sheet.save()
                equipment_type = None
                if Equipment.objects.filter(test_sheet__name=SHEET_TYPE_NAME).count() > 0:
                    equipment_type = Equipment.objects.filter(test_sheet__name=SHEET_TYPE_NAME).first()
                for n in range(form.cleaned_data['equipment_quantity']):
                    air_moving_equipment_equipment = AirMovingEquipment(sheet=sheet, equipment_type=equipment_type)
                    air_moving_equipment_equipment.save()
                return redirect('airMovingEquipmentSheetEquipmentList', sheet.id)
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'form': form,
        'orders': orders,
    }
    return render(request, "sheetAdd.html", parameters)


@login_required
def air_moving_equipment_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    project_name = request.GET.get('project_name', '')
    air_moving_equipment_equipments = AirMovingEquipment.objects.filter(sheet=my_sheet).order_by('id')
    if project_name:
        air_moving_equipment_equipments = air_moving_equipment_equipments.filter(Q(model_number__icontains=project_name)).distinct()
    parameters = {
        'sheet_type_name': SHEET_TYPE_NAME,
        'equipments': air_moving_equipment_equipments,
        'my_sheet': my_sheet,
        'sheet_id': sheet_id,
        'WEB_URL': WEB_URL,
        'MEDIA_URL': MEDIA_URL,
    }
    return render(request, "airMovingEquipmentSheetEquipmentsList.html", parameters)


@login_required
def air_moving_equipment_equipment_add(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    air_moving_equipment_equipment = AirMovingEquipment(sheet=my_sheet)
    air_moving_equipment_equipment.save()
    return redirect('airMovingEquipmentSheetEquipmentList', sheet_id)


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    total_pdf_row = 4
    my_sheet = DataSheet.objects.get(id=sheet_id)
    air_moving_equipment_equipments = AirMovingEquipment.objects.filter(sheet=my_sheet, design_data_entry_completed=True).order_by('id')
    if is_report_pdf:
        air_moving_equipment_equipments = air_moving_equipment_equipments.filter(actual_data_entry_completed=True)
    total_pages = math.ceil(air_moving_equipment_equipments.count() / total_pdf_row)
    air_moving_equipment_equipment_data = []
    air_moving_equipment_equipment_page = []
    i = 0
    for air_moving_equipment_equipment in air_moving_equipment_equipments:
        air_moving_equipment_equipment_obj = {}
        air_moving_equipment_equipment_obj['fan_no'] = air_moving_equipment_equipment.fan_no
        air_moving_equipment_equipment_obj['location'] = air_moving_equipment_equipment.location
        air_moving_equipment_equipment_obj['area_served'] = air_moving_equipment_equipment.area_served
        air_moving_equipment_equipment_obj['serial_number'] = air_moving_equipment_equipment.serial_number
        if air_moving_equipment_equipment.equipment:
            air_moving_equipment_equipment_obj['manufacturer'] = air_moving_equipment_equipment.equipment.manufacturer.name
            air_moving_equipment_equipment_obj['model_number'] = air_moving_equipment_equipment.equipment.model_number
        if is_report_pdf:
            air_moving_equipment_sheetdatas = air_moving_equipment_equipment.airmovingequipmentsheetdata_set.all()
        else:
            air_moving_equipment_sheetdatas = air_moving_equipment_equipment.airmovingequipmentsheetdata_set.filter(data_type=1)
        for air_moving_equipment_data in air_moving_equipment_sheetdatas:
            air_moving_equipment_equipment_obj[air_moving_equipment_data.sheet_field.field_name + '-' + str(air_moving_equipment_data.data_type)] = air_moving_equipment_data.value
        air_moving_equipment_equipment_page.append(air_moving_equipment_equipment_obj)
        i += 1
        if i == total_pdf_row:
            air_moving_equipment_equipment_data.append(air_moving_equipment_equipment_page)
            air_moving_equipment_equipment_page = []
            i = 0
    if air_moving_equipment_equipment_page:
        air_moving_equipment_equipment_data.append(air_moving_equipment_equipment_page)

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
        'empty_row_range': range(total_pdf_row - (air_moving_equipment_equipments.count() % total_pdf_row)),
        'form': {
            'total_pages_range': range(total_pages),
            'total_pages': total_pages,
            'my_sheet': my_sheet,
            'equipments': air_moving_equipment_equipments,
            'equipment_data': air_moving_equipment_equipment_data
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
        'WEB_URL': WEB_URL,
        'STATIC_URL': STATIC_URL,
        'MEDIA_URL': MEDIA_URL,
        'os': system(),
    }


@login_required
def equipments_generate_tech_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, False)
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/airMovingEquipmentSheetPDFTemplate.html', parameters,
                                                  'airMovingEquipmentPDFReport')

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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/airMovingEquipmentSheetPDFTemplate.html', parameters,
                                                  'airMovingEquipmentPDFReport')

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
def air_moving_equipment_common_data(request, air_moving_equipment_equipment_id):
    air_moving_equipment_equipment = get_object_or_404(AirMovingEquipment, id=air_moving_equipment_equipment_id)
    this_equipment = None
    if air_moving_equipment_equipment.equipment:
        this_equipment = air_moving_equipment_equipment.equipment
    form = AirMovingEquipmentSheetEquipmentForm(request.POST or None, request.FILES or None, instance=air_moving_equipment_equipment)
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=air_moving_equipment_equipment.equipment_type).distinct()
    equipment_db = EquipmentDb.objects.filter(equipment_type=air_moving_equipment_equipment.equipment_type)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)
        if form.is_valid():
            if request.POST.get("save"):
                form.cleaned_data['sheet'] = air_moving_equipment_equipment.sheet
                saving_obj = form.save(commit=False)
                saving_obj.main_data_entry_completed = True
                if request.POST.get("id_equipment"):
                    selected_equipment = EquipmentDb.objects.get(id=request.POST.get("id_equipment"))
                    saving_obj.equipment = selected_equipment
                saving_obj.save()
                return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)

    parameters = {
        'form': form,
        'equipment': air_moving_equipment_equipment,
        'manufacturers': manufacturers,
        'equipment_db': equipment_db,
        'this_equipment': this_equipment,
    }
    return render(request, "airMovingEquipmentSheetEquipmentGeneralData.html", parameters)


@login_required
def air_moving_equipment_design_data(request, air_moving_equipment_equipment_id):
    air_moving_equipment_equipment = get_object_or_404(AirMovingEquipment, id=air_moving_equipment_equipment_id)

    design_fields = TestSheetField.objects.filter(show_in_design=True, test_sheet__name__icontains=SHEET_TYPE_NAME)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)
        if request.POST.get("next"):

            for design_field in design_fields:
                new_value = request.POST.get(f'supply_design_value_{design_field.id}').strip()

                if air_moving_equipment_equipment.equipment:
                    if EquipmentDbDesignData.objects.filter(equipment=air_moving_equipment_equipment.equipment.id, key=design_field.id).exists():
                        db_data = EquipmentDbDesignData.objects.get(equipment=air_moving_equipment_equipment.equipment.id, key=design_field.id)
                        db_data.value = new_value
                        db_data.save()
                    else:
                        new_data = EquipmentDbDesignData(equipment=air_moving_equipment_equipment.equipment.id, key=design_field.id, value=new_value)
                        new_data.save()

                num_results = AirMovingSheetData.objects.filter(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                                           sheet_field=design_field).count()

                if num_results > 0:
                    AirMovingSheetData.objects.filter(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                                 sheet_field=design_field).update(value=new_value)
                else:
                    new_object = AirMovingSheetData(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                               sheet_field=design_field,
                                               value=new_value)
                    new_object.save()

            air_moving_equipment_equipment.design_data_entry_completed = True
            air_moving_equipment_equipment.save()
            return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)

    parameters = {
        'equipment': air_moving_equipment_equipment,
        'sheet_type_name': SHEET_TYPE_NAME,
        'design_fields': design_fields,
    }
    return render(request, "airMovingEquipmentSheetEquipmentDesignData.html", parameters)


@login_required
def air_moving_equipment_actual_data(request, air_moving_equipment_equipment_id):
    air_moving_equipment_equipment = get_object_or_404(AirMovingEquipment, id=air_moving_equipment_equipment_id)

    actual_fields = TestSheetField.objects.filter(show_in_actual=True, test_sheet__name__icontains=SHEET_TYPE_NAME)

    # assignment_operations = parse_assigment_operations_actual(air_moving_equipment_equipment, actual_fields)
    # show_parentheses_fields = get_show_parentheses_fields_actual(equipment_type_custom_fields, actual_fields)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)
        if request.POST.get("next"):

            for actual_field in actual_fields:
                if actual_field.field_type != 4:
                    new_value = request.POST.get(f'supply_actual_value_{actual_field.id}').strip()
                else:
                    new_value = request.POST.getlist(f'supply_actual_value_{actual_field.id}')
                    if new_value:
                        new_value = 1
                    else:
                        new_value = 0

                num_results = AirMovingSheetData.objects.filter(data_type=2, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                                           sheet_field=actual_field).count()

                if num_results > 0:
                    AirMovingSheetData.objects.filter(data_type=2, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                                 sheet_field=actual_field).update(value=new_value)
                else:
                    new_object = AirMovingSheetData(data_type=2, air_moving_equipment_equipment=air_moving_equipment_equipment,
                                               sheet_field=actual_field,
                                               value=new_value)
                    new_object.save()

            air_moving_equipment_equipment.actual_data_entry_completed = True
            air_moving_equipment_equipment.save()
            return redirect('airMovingEquipmentSheetEquipmentList', air_moving_equipment_equipment.sheet.id)

    design_hp = AirMovingSheetData.objects.get(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment, sheet_field__field_name__iexact='H.P.').value
    design_voltage = AirMovingSheetData.objects.get(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment, sheet_field__field_name__iexact='Voltage').value
    design_amperage = AirMovingSheetData.objects.get(data_type=1, air_moving_equipment_equipment=air_moving_equipment_equipment, sheet_field__field_name__iexact='Amperage').value
    parameters = {
        'design_hp': design_hp,
        'design_voltage': design_voltage,
        'design_amperage': design_amperage,
        'equipment': air_moving_equipment_equipment,
        'sheet_type_name': SHEET_TYPE_NAME,
        'actual_fields': actual_fields,
    }
    return render(request, "airMovingEquipmentSheetEquipmentActualData.html", parameters)


@login_required
def air_moving_equipment_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('airMovingEquipmentSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('airMovingEquipmentSheetHome')
    parameters = {
        'this_sheet': this_sheet,
        'sheet_type_name': SHEET_TYPE_NAME,
    }
    return render(request, "sheetDelete.html", parameters)


def parse_assigment_operations_actual(this_sheet_equipment, custom_fields, insert=True):
    assignment_operations = this_sheet_equipment.sheet.test_sheet_type.actualdatacustomoperation_set.filter(operand_type=OperandChoices.AssignTo.value)

    print(assignment_operations)
    assignments = []
    result_field_regex = re.compile(r'\[field-[\d]+-actual]', re.I)
    expression_regex = re.compile(r'\[field-[\d]+-(actual|design)]', re.I)
    actual_field_id_matches: Dict[int, int] = {}
    design_values_matches: Dict[int, str] = {}

    def get_related_id(equipment_type_custom_field_id: int) -> int:
        """Finds and caches the actual value field id"""
        related_id = actual_field_id_matches.get(equipment_type_custom_field_id)
        if related_id is None:
            equipment_type_custom_field = equipment_type_custom_fields.get(pk=equipment_type_custom_field_id)
            if insert:
                custom_field = custom_fields.get(equipment_value_name=equipment_type_custom_field.field_name)
            else:
                custom_field = custom_fields.get(key__equipment_value_name=equipment_type_custom_field.field_name)
            related_id = custom_field.id
            actual_field_id_matches[equipment_type_custom_field_id] = related_id
        return related_id

    def get_related_value(equipment_type_custom_field_id: int) -> str:
        """Finds and caches the design value"""
        related_value = design_values_matches.get(equipment_type_custom_field_id)
        if related_value is None:
            equipment_type_custom_field = equipment_type_custom_fields.get(pk=equipment_type_custom_field_id)
            if insert:
                custom_field = custom_fields.get(equipment_value_name=equipment_type_custom_field.field_name)
            else:
                custom_field = custom_fields.get(key__equipment_value_name=equipment_type_custom_field.field_name).key
            related_value = custom_field.company_value
            if '-' in related_value:
                related_value = related_value.replace(' ', '').replace('-', ',')
                related_value = '{' + str(get_related_id(equipment_type_custom_field.id)) + ',' + related_value + '}'
            design_values_matches[equipment_type_custom_field_id] = related_value
        return related_value

    def replace(match):
        """
        Replaces `actual` matches with `$('[name="actual_value_[FIELD ID]"]').val()` and
        `design` matches with design value.
        """
        group = match.group()
        field_id = int(group[7:-8])
        if group[-2] == 'l' or group[-2] == 'L':
            # this group is like [field-[FIELD ID]-actual]
            return '$(\'[name="actual_value_{}"]\').val()'.format(get_related_id(field_id))
        else:
            # this group is like [field-[FIELD ID]-design]
            return get_related_value(field_id)

    for assignment in assignment_operations:
        if assignment.result_field and assignment.operation:
            result_field = assignment.result_field.strip()
            if re.fullmatch(result_field_regex, result_field):
                result_field_id = int(result_field[result_field.find('-') + 1:result_field.rfind('-')])
                result_field_id = get_related_id(result_field_id)
                left_side_of_assignment = '$(\'[name="actual_value_{}"]\')'.format(result_field_id)
                operation = assignment.operation.strip()
                operation = re.sub(expression_regex, replace, operation)
                final_expression = '{}.val({})'.format(left_side_of_assignment, operation)
                assignments.append(final_expression)
    return assignments


def get_show_parentheses_fields_actual(equipment_type_custom_fields, custom_fields, insert=True):
    require_parentheses = equipment_type_custom_fields.filter(Q(show_parentheses=ShowParenthesesChoices.Actual.value) |
                                                              Q(show_parentheses=ShowParenthesesChoices.Both.value))
    if insert:
        fields = map(lambda item: {
            'id': f'actual_value_{custom_fields.get(equipment_value_name=item.field_name).id}',
            'defaultValue': item.default_value,
        }, require_parentheses)
    else:
        fields = map(lambda item: {
            'id': f'actual_value_{custom_fields.get(key__equipment_value_name=item.field_name).id}',
            'defaultValue': item.default_value,
        }, require_parentheses)
    return list(fields)
