from platform import system
import re
from typing import Dict
import math
import os
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from .render import Render as PDFRender
from ..sheetcreator.models import *
from itertools import chain
from django.http import JsonResponse


# Create your views here.


@login_required
def vav_sheet_list(request):
    search = request.GET.get('search', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheet.objects.filter(test_sheet_type__name__iexact='vav')
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=search) |
                                     Q(project__project_number__icontains=search)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "vavList.html", parameters)


@login_required
def vav_sheet_add(request):
    form = VavSheetForm(request.POST or None, request.FILES or None)
    orders = Order.objects.exclude(id__in=DataSheet.objects.filter(test_sheet_type__name__iexact='vav').values_list('project_id')).order_by('-project_number')
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vavSheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(name__iexact='vav')
                sheet.save()
                return redirect('vavSheetEquipment', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "vavSheetAdd.html", parameters)


@login_required
def vav_sheet_equipment(request, sheet_id):
    sheet = DataSheet.objects.get(id=sheet_id)
    form = VavSheetEquipmentForm(request.POST or None, initial={'sheet': sheet_id})

    equipments = Equipment.objects.filter(Q(test_sheet__name__iexact='vav') | Q(test_sheet__inheritance__name__iexact='vav'))

    equipment_in = []
    sheet_equipments = DataSheetEquipment.objects.filter(sheet=sheet_id)
    for one_sheet_equipment in sheet_equipments:
        equipment_in.append(one_sheet_equipment.equipment_type.id)

    equipments_count = {}
    for one_sheet_equipment in sheet_equipments:
        if one_sheet_equipment.equipment_type.name in equipments_count:
            old_quantity = equipments_count[one_sheet_equipment.equipment_type.name]
            new_quantity = old_quantity + 1
            equipments_count[one_sheet_equipment.equipment_type.name] = new_quantity
        else:
            equipments_count[one_sheet_equipment.equipment_type.name] = 1
    if request.method == 'POST':
        if form.is_valid():
            form.cleaned_data['sheet'] = sheet_id
            if DataSheetEquipment.objects.filter(sheet=sheet_id,
                                                 equipment_type=form.cleaned_data['equipment_type']).count() != 0:
                DataSheetEquipment.objects.filter(sheet=sheet_id,
                                                  equipment_type=form.cleaned_data['equipment_type']).delete()
            for i in range(0, form.cleaned_data['quantity']):
                item_sheet_equipment = DataSheetEquipment()
                item_sheet_equipment.sheet = DataSheet.objects.get(id=sheet_id)
                item_sheet_equipment.equipment_type = Equipment.objects.get(id=form.cleaned_data['equipment_type'].id)
                item_sheet_equipment.save()
            return redirect('vavSheetEquipment', sheet_id)

    first_equipment = sheet_equipments.first()
    if first_equipment is None:
        any_equipment_id = False
    else:
        any_equipment_id = True

    parameters = {'sheet': sheet,
                  'form': form,
                  'sheet_equipments': sheet_equipments,
                  'equipment_in': equipment_in,
                  'equipments_count': equipments_count,
                  'equipments': equipments,
                  'any_equipment_id': any_equipment_id,
                  }
    return render(request, "vavSheetEquipment.html", parameters)


@login_required
def vav_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    project_name = request.GET.get('project_name', '')

    pagination = 50
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    object_list = DataSheetEquipment.objects.filter(sheet=sheet_id)
    search_lowercase = project_name.lower()
    search_contains_letters = search_lowercase.islower()
    if project_name:
        if search_contains_letters:
            object_list = object_list.filter(testsheetgeneraldata__value__icontains=project_name)
        else:
            object_list = object_list.filter(Q(testsheetgeneraldata__value__icontains=project_name) | Q(id=project_name))
    object_list = object_list.order_by('main_data_entry_completed', 'design_data_entry_completed', 'actual_data_entry_completed', 'field_order')

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheet_equipments': sheets,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "vavSheetEquipmentsList.html", parameters)


@login_required
def sort_vav_sheet_equipment_list(request, sheet_id):
    my_sheet = DataSheet.objects.get(id=sheet_id)

    project_name = request.GET.get('project_name', '')

    pagination = 500
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = 'field_order'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = DataSheetEquipment.objects.filter(sheet=sheet_id)
    search_lowercase = project_name.lower()
    search_contains_letters = search_lowercase.islower()
    if project_name:
        if search_contains_letters:
            object_list = object_list.filter(testsheetgeneraldata__value__icontains=project_name)
        else:
            object_list = object_list.filter(Q(testsheetgeneraldata__value__icontains=project_name) | Q(id=project_name))
    object_list = object_list.order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheet_equipments': sheets,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "sortVavSheetEquipmentsList.html", parameters)


@login_required
def update_sheet_equipments_positioning(request, sheet_id):
    if request.method == "POST" and request.is_ajax():
        sheet_equipments_array = request.POST.getlist('sheetEquipmentsArray[]')
        sheet_equipments = DataSheetEquipment.objects.filter(sheet=sheet_id)
        i = 1
        for equipment_id in sheet_equipments_array:
            equipment = sheet_equipments.get(id=equipment_id)
            equipment.field_order = i
            equipment.save()
            i = i+1
        return JsonResponse({
            'result': True,
            'msg': 'Equipments Positioning Successfully Updated!'
        })
    else:
        status = "Bad"
        return JsonResponse(status, safe=False)


def fetch_sheet_equipment_data(this_sheet_equipment: DataSheetEquipment, is_report_pdf: bool):
    general_fields = TestSheetColumn.objects.filter(test_sheet__name__iexact='vav')
    general_data = TestSheetGeneralData.objects.filter(sheet_equipment=this_sheet_equipment)
    inherit = False
    if this_sheet_equipment.equipment_type.test_sheet.inheritance:
        inherit = True
    equipment_data = {
        'inherit': inherit,
        'code': general_data.get(key=general_fields.get(column_title__iexact='code')).value,
    }

    design_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_design=True)
    design_data = [
        ('type', 'type'),
        ('size', 'size'),
        ('kw', 'kw'),
        ('fan_cfm', 'fan cfm'),
        ('min_cfm', 'min. cfm'),
        ('max_cfm', 'max. cfm'),
    ]
    equipment_data['design'] = {}
    for key, val in design_data:
        design_field = design_fields.get(field_name__iexact=val)
        if this_sheet_equipment.equipment:
            design_value = EquipmentDbDesignData.objects.get(equipment=this_sheet_equipment.equipment,
                                                             key=design_field).value
        else:
            design_value = TestSheetData.objects.get(data_type=DataTypeChoices.Design.value, sheet_field=design_field,
                                                     sheet_equipment=this_sheet_equipment).value
        equipment_data['design'][key] = design_value

    if is_report_pdf:
        actual_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_actual=True)
        actual_data = [
            ('kf', 'k.f.'),
            ('fan_cfm', 'fan cfm'),
            ('min_cfm', 'min. cfm'),
            ('max_cfm', 'max. cfm'),
            ('address', 'address'),
            ('note', 'note'),
        ]
        equipment_data['actual'] = {}
        for key, val in actual_data:
            actual_field = actual_fields.get(field_name__iexact=val)
            actual_value = TestSheetData.objects.get(data_type=DataTypeChoices.Actual.value, sheet_field=actual_field,
                                                     sheet_equipment=this_sheet_equipment).value
            equipment_data['actual'][key] = actual_value

        if this_sheet_equipment.equipment_type.test_sheet.inheritance:
            if this_sheet_equipment.equipment_type.test_sheet.inheritance.name.lower() == 'vav':
                actual_fields = this_sheet_equipment.equipment_type.test_sheet.testsheetfield_set.filter(
                    show_in_actual=True)
                actual_data = [
                    ('nameplate_fan_volt', 'nameplate fan volt'),
                    ('nameplate_fan_amp', 'nameplate fan amp'),
                    ('nameplate_heat_va', 'nameplate heat v/a'),
                    ('t_in', 't in'),
                    ('fan_va', 'fan v/a'),
                    ('heat_va', 'heat v/a'),
                    ('t_out', 't out'),
                    ('model', 'model'),
                    ('note', 'note'),
                ]
                equipment_data['vavp'] = {}
                for key, val in actual_data:
                    actual_field = actual_fields.get(field_name__iexact=val)
                    actual_value = TestSheetData.objects.get(data_type=DataTypeChoices.Actual.value,
                                                             sheet_field=actual_field,
                                                             sheet_equipment=this_sheet_equipment).value
                    equipment_data['vavp'][key] = actual_value

    return equipment_data


def get_pdf_empty_row():
    return {
        'code': '',
        'design': {
            'type': '',
            'size_kw': '',
            'fan_cfm': '',
            'min_cfm': '',
            'max_cfm': '',
        },
        'actual': {
            'address': '',
            'kf': '',
            'min_fan_cfm': '',
            'max_cfm': '',
            'nameplate_fan_volt': '',
            'nameplate_fan_amp': '',
            'nameplate_heat_va': '',
            't_in': '',
            'fan_va': '',
            'a_heat_va': '',
            't_out': '',
            'model': '',
            'note': '',
        },
    }


def get_pdf_parameters(sheet_id, is_report_pdf: bool):
    my_sheet = DataSheet.objects.get(id=sheet_id)
    sheet_equipments = DataSheetEquipment.objects.filter(sheet=my_sheet, main_data_entry_completed=True,
                                                         design_data_entry_completed=True)

    vavp_available = False

    if is_report_pdf:
        sheet_equipments = sheet_equipments.filter(actual_data_entry_completed=True)

    data = []
    equipment_groups = list(map(lambda x: chr(x), range(65, 65 + my_sheet.number_of_equipment_groups)))
    equipment_in_page = 22
    last_loop = 0
    for group in equipment_groups:
        group_equipments = sheet_equipments.filter(equipment_group=group)
        len_equipments = group_equipments.count()
        for i in range(math.ceil(len_equipments / equipment_in_page)):
            last_loop += 1
            page = {'rows': [], 'notes': [], 'vavp_available': 0}
            for j in range(equipment_in_page):
                index = i * equipment_in_page + j
                if index < len_equipments:
                    page['rows'].append(fetch_sheet_equipment_data(group_equipments[index], is_report_pdf))
                    if group_equipments[index].equipment_type.test_sheet.inheritance:
                        page['vavp_available'] = 1
                else:
                    page['rows'].append(get_pdf_empty_row())
            if page['rows']:
                data.append(page)

    if len(data) == 0:
        data.append([])

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
        'form': {
            'my_sheet': my_sheet,
            'vavp_available': vavp_available,
            'data': data,
            'last_loop': last_loop,
        },
        'file_name': 'V.A.V. BOX SCHEDULE {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/vavSheetEquipmentTechTemplate.html', parameters,
                                                  'vavEquipmentReport')
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            return response
    else:
        return 'error'


@login_required
def equipments_generate_report_pdf(request, sheet_id):
    parameters = get_pdf_parameters(sheet_id, True)
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/vavSheetEquipmentTemplate.html', parameters,
                                                  'vavEquipmentReport')

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
def vav_sheet_equipment_general_data(request, sheet_equipment_id):
    next_url = request.GET.get("next")
    sheet_equipment = DataSheetEquipment.objects.get(id=sheet_equipment_id)
    showing_fields = TestSheetColumn.objects.filter(test_sheet__name__iexact='vav')
    manufacturers = EquipmentManufacturer.objects.filter(
        equipmentdb__equipment_type=sheet_equipment.equipment_type).distinct()
    Equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__iexact='vav',
                                              equipment_type=sheet_equipment.equipment_type)

    sat = sheet_equipment.number_of_supply_air_terminal

    equipments = Equipment.objects.filter(test_sheet__name__iexact='vav')

    equipment_groups = list(map(lambda x: chr(x), range(65, 65 + sheet_equipment.sheet.number_of_equipment_groups)))

    value_fields = TestSheetGeneralData.objects.filter(sheet_equipment_id=sheet_equipment_id)
    edit_page = False
    if value_fields.exists():
        edit_page = True

    if request.method == 'POST':
        if request.POST.get("cancel"):
            if next_url:
                return redirect(WEB_URL + next_url)
            return redirect('vavSheetEquipmentList', sheet_equipment.sheet.id)
        if edit_page:
            for value_field in value_fields:
                TestSheetGeneralData.objects.filter(key=value_field.key,
                                                    sheet_equipment=sheet_equipment).update(
                    value=request.POST.get('showing_field_value_' + str(value_field.id)))
            if request.POST.get('id_equipment'):
                sheet_equipment.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
            sheet_equipment.equipment_group = request.POST.get('equipment_group')
            old_supply_number = sheet_equipment.number_of_supply_air_terminal
            sheet_equipment.number_of_supply_air_terminal = request.POST.get('number_of_supply_air_terminal')
            if int(old_supply_number) != int(request.POST.get('number_of_supply_air_terminal')):
                if int(old_supply_number) > int(request.POST.get('number_of_supply_air_terminal')):
                    AirTerminalEquipment.objects.filter(vav_equipment=sheet_equipment).delete()
                sheet_equipment.terminal_design_data_entry_completed = False
                sheet_equipment.terminal_actual_data_entry_completed = False
            sheet_equipment.save()
            if next_url:
                return redirect(WEB_URL + next_url)
            return redirect('vavSheetEquipmentList', sheet_equipment.sheet.id)
        else:
            for every_field in showing_fields:
                key = every_field
                field_value = request.POST.get('showing_field_value_' + str(every_field.id))
                new_record = TestSheetGeneralData(sheet_equipment_id=sheet_equipment_id, key=key, value=field_value)
                new_record.save()
            new_update = DataSheetEquipment.objects.get(id=sheet_equipment_id)
            if request.POST.get('id_equipment'):
                new_update.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
            new_update.equipment_group = request.POST.get('equipment_group')
            new_update.number_of_supply_air_terminal = request.POST.get('number_of_supply_air_terminal')
            new_update.main_data_entry_completed = True
            new_update.save()
        return redirect('vavSheetEquipmentList', sheet_equipment.sheet.id)

    parameters = {
        'sat': sat,
        'sheet_equipment': sheet_equipment,
        'showing_fields': showing_fields,
        'value_fields': value_fields,
        'equipment_groups': equipment_groups,
        'manufacturers': manufacturers,
        'Equipment_db': Equipment_db,
        'edit_page': edit_page,
    }

    return render(request, "vavSheetEquipmentGeneralData.html", parameters)


def split(value: str, sep: str):
    return value.replace(' ', '').split(sep)


def contains(value: str, sub: str):
    return value.find(sub) != -1


def find_closest_design_value(actual_value: str, design_value: str, sep: str):
    if contains(design_value, sep):
        splitted = split(design_value, sep)
        if actual_value and actual_value.strip():
            actual_value = eval(actual_value.strip())
            return min(splitted, key=lambda x: abs(float(x) - actual_value))
        else:
            return splitted[0]
    return design_value


def get_show_parentheses_fields(this_sheet_equipment: DataSheetEquipment, is_design_form: bool):
    fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set
    if is_design_form:
        field_name_prefix = 'company_value_'
        fields = fields.filter(show_in_design=True).filter(
            Q(show_parentheses=ShowParenthesesChoices.Design.value) |
            Q(show_parentheses=ShowParenthesesChoices.Both.value)
        )
    else:
        field_name_prefix = 'actual_value_'
        fields = fields.filter(show_in_actual=True).filter(
            Q(show_parentheses=ShowParenthesesChoices.Actual.value) |
            Q(show_parentheses=ShowParenthesesChoices.Both.value)
        )
    return list(map(lambda item: {'id': f'{field_name_prefix}{item.id}', 'defaultValue': item.default_value}, fields))


def get_assigment_operations(this_sheet_equipment: DataSheetEquipment, is_design_form: bool):
    is_actual_form = not is_design_form

    design_field_regex = re.compile(r'\[field-[\d]+-design]', re.I)
    actual_field_regex = re.compile(r'\[field-[\d]+-actual]', re.I)
    design_field_name_prefix = 'company_value_'
    actual_field_name_prefix = 'actual_value_'

    test_sheet_operations = this_sheet_equipment.sheet.test_sheet_type.testsheetoperation_set
    design_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_design=True)

    if is_design_form:
        field_regex = design_field_regex
        field_name_prefix = design_field_name_prefix
        custom_operations = test_sheet_operations.filter(apply_on_design=True)
    else:
        field_regex = actual_field_regex
        field_name_prefix = actual_field_name_prefix
        custom_operations = test_sheet_operations.filter(apply_on_actual=True)

    def replace_design_values(expression):
        def get_design_value(m):
            field_id = m.group()[7:-8]
            design_field = design_fields.get(pk=field_id)
            if this_sheet_equipment.equipment:
                design_value = EquipmentDbDesignData.objects.get(equipment=this_sheet_equipment.equipment,
                                                                 key=design_field).value
            else:
                design_value = TestSheetData.objects.get(data_type=DataTypeChoices.Design.value,
                                                         sheet_field=design_field,
                                                         sheet_equipment=this_sheet_equipment).value
            if contains(design_value, '-'):
                design_value = design_value.replace(' ', '').replace('-', ',')
                design_value = '{' + field_id + ',' + design_value + '}'
            return design_value

        expression = re.sub(design_field_regex, get_design_value, expression)
        return expression

    def jquery_selector(field_regex_matched):
        name = f'{field_name_prefix}{field_regex_matched[7:-8]}'
        return f'$(\'[name="{name}"]\')'

    assignment_operations = custom_operations.filter(operand_type=OperandChoices.AssignTo.value)
    assignments = []
    for assignment in assignment_operations:
        left_side = assignment.operation.strip().lower()
        right_side = assignment.result_field.strip().lower()

        # ignore assignment when:
        #
        #                               | left_side has 'actual' word
        #       | is_design_form and ---  OR
        #       |                       | right_side does not matches [field-ID-design]
        # if ---  OR
        #       |
        #       | is_actual_form and right_side does not matches [field-ID-actual]
        #
        if (is_design_form and (contains(left_side, 'actual') or not re.fullmatch(design_field_regex, right_side))) or \
                (is_actual_form and not re.fullmatch(actual_field_regex, right_side)):
            continue

        try:
            left_side = re.sub(field_regex, lambda m: f'parseFloat({jquery_selector(m.group())}.val())', left_side)

            # when is_actual_form and the formula has design fields
            # replace design fields in the formula with design values previously saved in the database
            if is_actual_form and contains(left_side, 'design'):
                left_side = replace_design_values(left_side)

            final_expression = f'{jquery_selector(right_side)}.val({left_side})'
            assignments.append(final_expression)
        except:
            continue
    return assignments


def check_form_values(request, this_sheet_equipment: DataSheetEquipment, is_design_form: bool):
    is_actual_form = not is_design_form

    design_field_regex = re.compile(r'\[field-[\d]+-design]', re.I)
    actual_field_regex = re.compile(r'\[field-[\d]+-actual]', re.I)
    design_field_name_prefix = 'company_value_'
    actual_field_name_prefix = 'actual_value_'

    test_sheet_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set
    test_sheet_operations = this_sheet_equipment.sheet.test_sheet_type.testsheetoperation_set
    design_fields = test_sheet_fields.filter(show_in_design=True)

    if is_design_form:
        field_regex = design_field_regex
        field_name_prefix = design_field_name_prefix
        form_fields = test_sheet_fields.filter(show_in_design=True)
        custom_operations = test_sheet_operations.filter(apply_on_design=True)
    else:
        field_regex = actual_field_regex
        field_name_prefix = actual_field_name_prefix
        form_fields = test_sheet_fields.filter(show_in_actual=True)
        custom_operations = test_sheet_operations.filter(apply_on_actual=True)

    def replace_design_values(expression, expression_msg):
        def get_design_value(m):
            field_id = m.group()[7:-8]
            actual_value = request.POST.get(f'{actual_field_name_prefix}{field_id}')
            design_field = design_fields.get(pk=field_id)
            if this_sheet_equipment.equipment:
                design_value = EquipmentDbDesignData.objects.get(equipment=this_sheet_equipment.equipment,
                                                                 key=design_field).value
            else:
                design_value = TestSheetData.objects.get(data_type=DataTypeChoices.Design.value,
                                                         sheet_field=design_field,
                                                         sheet_equipment=this_sheet_equipment).value
            return find_closest_design_value(actual_value, design_value, '-')

        expression = re.sub(design_field_regex, get_design_value, expression)
        expression_msg = re.sub(design_field_regex,
                                lambda m: design_fields.get(pk=m.group()[7:-8]).field_name + ' (design)',
                                expression_msg)
        return expression, expression_msg

    # validate field value range
    conv_to_num = None
    for field in form_fields:
        if field.field_type == FieldTypeChoices.Characters.value:
            continue
        elif field.field_type == FieldTypeChoices.Integer.value:
            conv_to_num = int
        elif field.field_type == FieldTypeChoices.Float.value:
            conv_to_num = float

        if request.POST.get(f'{field_name_prefix}{field.id}'):
            try:
                form_field_value = conv_to_num(request.POST.get(f'{field_name_prefix}{field.id}'))
            except ValueError:
                print(ValueError)
                return f'{field.field_name} value is not valid. The value must be ' \
                       f'{"integer" if conv_to_num == int else "float"} number.'

            if field.field_range_or_selective == FieldRangeOrSelectiveChoices.Range.value:
                field_range = split(field.field_range, '-')
                min_value = conv_to_num(field_range[0])
                max_value = conv_to_num(field_range[1])
                if form_field_value < min_value or max_value < form_field_value:
                    return f'{field.field_name} value is not in range. Valid range is {field.field_range}.'
            elif field.field_range_or_selective == FieldRangeOrSelectiveChoices.Selective.value:
                field_range = split(field.field_range, ',')
                if form_field_value not in map(lambda x: conv_to_num(x), field_range):
                    return f'{field.field_name} value is not selected right. Valid choices are {field.field_range}.'

    # check custom operations
    custom_operations = custom_operations.filter(~Q(operand_type=OperandChoices.AssignTo.value))
    for custom_operation in custom_operations:
        left_side = left_side_msg = custom_operation.operation.strip().lower()
        right_side = right_side_msg = custom_operation.result_field.strip().lower()

        # ignore custom_operation when:
        #
        #                               | left_side has 'actual' word
        #       | is_design_form and ---  OR
        #       |                       | right_side does not matches [field-ID-design]
        # if ---  OR
        #       |
        #       | is_actual_form and right_side does not matches [field-ID-actual]
        #
        if (is_design_form and (contains(left_side, 'actual') or not re.fullmatch(design_field_regex, right_side))) or \
                (is_actual_form and not re.fullmatch(actual_field_regex, right_side)):
            continue

        try:
            # if is_design_form then replace design fields in formula with their form values
            # else if is_actual_form then replace actual fields in formula with their form values
            left_side = re.sub(field_regex, lambda m: request.POST.get(f'{field_name_prefix}{m.group()[7:-8]}'),
                               left_side)
            left_side_msg = re.sub(field_regex, lambda m: form_fields.get(pk=m.group()[7:-8]).field_name, left_side_msg)
            right_side = request.POST.get(f'{field_name_prefix}{right_side[7:-8]}')
            right_side_msg = form_fields.get(pk=right_side_msg[7:-8]).field_name

            # when is_actual_form and the formula has design fields
            # replace design fields in the formula with design values previously saved in the database
            if is_actual_form and contains(left_side, 'design'):
                left_side, left_side_msg = replace_design_values(left_side, left_side_msg)

            left_side = eval(left_side)
            right_side = eval(right_side)
            if custom_operation.operand_type == OperandChoices.EqualTo.value:
                if left_side != right_side:
                    return f'{left_side_msg} must be equal to {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.GreaterThan.value:
                if left_side <= right_side:
                    return f'{left_side_msg} must be greater than {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.GreaterOrEqualTo.value:
                if left_side < right_side:
                    return f'{left_side_msg} must be greater than or equal to {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.SmallerThan.value:
                if left_side >= right_side:
                    return f'{left_side_msg} must be smaller than {right_side_msg}'
            elif custom_operation.operand_type == OperandChoices.SmallerOrEqualTo.value:
                if left_side > right_side:
                    return f'{left_side_msg} must be smaller than or equal to {right_side_msg}'
        except:
            continue

    return None


@login_required
def vav_sheet_equipment_design_data(request, sheet_equipment_id):
    this_sheet_equipment = get_object_or_404(DataSheetEquipment, id=sheet_equipment_id)
    design_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_design=True)
    show_parentheses_fields = get_show_parentheses_fields(this_sheet_equipment, True)
    assignment_operations = get_assigment_operations(this_sheet_equipment, True)

    sheet_code = this_sheet_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vavSheetEquipmentList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            error_msg = check_form_values(request, this_sheet_equipment, True)
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'design_fields': design_fields,
                    'show_parentheses_fields': show_parentheses_fields,
                    'assignment_operations': assignment_operations,
                    'error_msg': error_msg,
                    'sheet_code': sheet_code,
                }
                return render(request, "vavSheetEquipmentDesignData.html", parameters)

            # if no error save design values
            for design_field in design_fields:
                new_value = request.POST.get(f'company_value_{design_field.id}').strip()

                # if Manufacturer and Model Number selected, Update Design values in EquipmentDbDesignData Table
                if this_sheet_equipment.equipment:
                    equipment_db_design_value = EquipmentDbDesignData.objects.filter(
                        equipment=this_sheet_equipment.equipment, key=design_field)
                    if equipment_db_design_value.exists():
                        EquipmentDbDesignData.objects.filter(equipment=this_sheet_equipment.equipment,
                                                             key=design_field).update(value=new_value)
                    else:
                        new_object = EquipmentDbDesignData(equipment=this_sheet_equipment.equipment, key=design_field,
                                                           value=new_value)
                        new_object.save()

                # else if Manufacturer and Model Number not selected, Create or Update Design values in TestSheetData
                else:
                    num_results = TestSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                               sheet_field=design_field,
                                                               sheet_equipment=this_sheet_equipment).count()
                    if num_results > 0:
                        TestSheetData.objects.filter(data_type=DataTypeChoices.Design.value, sheet_field=design_field,
                                                     sheet_equipment=this_sheet_equipment).update(value=new_value)
                    else:
                        new_object = TestSheetData(sheet_field=design_field, sheet_equipment=this_sheet_equipment,
                                                   value=new_value)
                        new_object.save()
            this_sheet_equipment.design_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('vavSheetEquipmentList', this_sheet_equipment.sheet.id)
    parameters = {
        'this_sheet_equipment': this_sheet_equipment,
        'design_fields': design_fields,
        'show_parentheses_fields': show_parentheses_fields,
        'assignment_operations': assignment_operations,
        'sheet_code': sheet_code,
    }
    return render(request, "vavSheetEquipmentDesignData.html", parameters)


@login_required
def vav_sheet_equipment_actual_data(request, sheet_equipment_id):
    this_sheet_equipment = DataSheetEquipment.objects.get(id=sheet_equipment_id)
    actual_fields = this_sheet_equipment.sheet.test_sheet_type.testsheetfield_set.filter(show_in_actual=True)
    if this_sheet_equipment.equipment_type.test_sheet.inheritance:
        if this_sheet_equipment.equipment_type.test_sheet.inheritance.name.lower() == 'vav':
            actual_fields2 = this_sheet_equipment.equipment_type.test_sheet.testsheetfield_set.filter(show_in_actual=True)
            actual_fields = list(chain(actual_fields, actual_fields2))
    show_parentheses_fields = get_show_parentheses_fields(this_sheet_equipment, False)
    assignment_operations = get_assigment_operations(this_sheet_equipment, False)

    sheet_code = this_sheet_equipment.testsheetgeneraldata_set.get(key__column_title__icontains='code').value

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vavSheetEquipmentList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            error_msg = check_form_values(request, this_sheet_equipment, False)
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'actual_fields': actual_fields,
                    'show_parentheses_fields': show_parentheses_fields,
                    'assignment_operations': assignment_operations,
                    'error_msg': error_msg,
                }
                return render(request, "vavSheetEquipmentActualData.html", parameters)

            for actual_field in actual_fields:
                new_value = request.POST.get(f'actual_value_{actual_field.id}').strip()

                num_results = TestSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                           sheet_field=actual_field,
                                                           sheet_equipment=this_sheet_equipment).count()

                if num_results > 0:
                    TestSheetData.objects.filter(data_type=DataTypeChoices.Actual.value, sheet_field=actual_field,
                                                 sheet_equipment=this_sheet_equipment).update(value=new_value)
                else:
                    new_object = TestSheetData(data_type=DataTypeChoices.Actual.value, sheet_field=actual_field,
                                               sheet_equipment=this_sheet_equipment, value=new_value)
                    new_object.save()
            this_sheet_equipment.actual_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('vavSheetEquipmentList', this_sheet_equipment.sheet.id)

    parameters = {
        'this_sheet_equipment': this_sheet_equipment,
        'actual_fields': actual_fields,
        'show_parentheses_fields': show_parentheses_fields,
        'assignment_operations': assignment_operations,
        'sheet_code': sheet_code,
    }
    return render(request, "vavSheetEquipmentActualData.html", parameters)


@login_required
def vav_sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(DataSheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('vavSheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('vavSheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "vavSheetDelete.html", parameters)


@login_required
def vav_sheet_equipment_delete(request, sheet_id, sheet_equipment_name):
    this_sheet = DataSheetEquipment.objects.filter(equipment_type__name__iexact=sheet_equipment_name, sheet=sheet_id)
    if request.POST.get("confirm"):
        this_sheet.delete()
        return redirect('vavSheetEquipment', sheet_id)
    if request.POST.get("cancel"):
        return redirect('vavSheetEquipment', sheet_id)
    parameters = {'this_sheet': this_sheet,
                  'sheet_equipment_name': sheet_equipment_name,
                  }
    return render(request, "vavSheetEquipmentDelete.html", parameters)
