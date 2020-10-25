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
from ..order.models import *
from ..dbmanagement.models import FieldTypeChoices, FieldRangeOrSelectiveChoices, OperandChoices, ShowParenthesesChoices
from .forms import *
from ..settings import MEDIA_URL, WEB_URL, STATIC_URL
from .models import *
from .render import Render as PDFRender


# Create your views here.


@login_required
def sheet_list(request):
    project_name = request.GET.get('project_name', '')

    pagination = 20
    if request.GET.get('paginate_by'):
        pagination = request.GET.get('paginate_by')

    ordering = '-sheet_date'
    if request.GET.get('ordering'):
        ordering = request.GET.get('ordering')

    object_list = Sheet.objects.filter(test_sheet_type_id=1)
    object_list = object_list.filter(Q(project__proposal__quote__estimate__project__name__icontains=project_name) |
                                     Q(project__project_number__icontains=project_name)).order_by(ordering)

    paginator = Paginator(object_list, pagination)
    page = request.GET.get('page')
    sheets = paginator.get_page(page)

    parameters = {'sheets': sheets,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "sheetList.html", parameters)


@login_required
def sheet_add(request):
    form = SheetForm(request.POST or None, request.FILES or None, initial={'test_sheet_type': 1})
    orders = Order.objects.exclude(id__in=Sheet.objects.filter(test_sheet_type_id=1).values_list('project_id'))
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetHome')
        if form.is_valid():
            if request.POST.get("next"):
                sheet = form.save(commit=False)
                sheet.test_sheet_type = TestSheet.objects.get(pk=1)
                sheet.save()
                return redirect('sheetEquipment', sheet.id)
    parameters = {'form': form,
                  'orders': orders,
                  }
    return render(request, "sheetAdd.html", parameters)


@login_required
def sheet_equipment(request, sheet_id):
    sheet = Sheet.objects.get(id=sheet_id)
    form = SheetEquipmentForm(request.POST or None, initial={'sheet': sheet_id})

    equipments = Equipment.objects.filter(test_sheet__name__icontains='air mov')

    equipment_in = []
    sheet_equipments = SheetEquipment.objects.filter(sheet=sheet_id)
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
            if SheetEquipment.objects.filter(sheet=sheet_id, equipment_type=form.cleaned_data['equipment_type']).count() == 0:
                form.cleaned_data['sheet'] = sheet_id
                for i in range(0, form.cleaned_data['quantity']):
                    item_sheet_equipment = SheetEquipment()
                    item_sheet_equipment.sheet = Sheet.objects.get(id=sheet_id)
                    item_sheet_equipment.equipment_type = Equipment.objects.get(id=form.cleaned_data['equipment_type'].id)
                    item_sheet_equipment.save()
                return redirect('sheetEquipment', sheet_id)
            else:
                SheetEquipment.objects.filter(sheet=sheet_id, equipment_type=form.cleaned_data['equipment_type']).delete()
                for i in range(0, form.cleaned_data['quantity']):
                    item_sheet_equipment = SheetEquipment()
                    item_sheet_equipment.sheet = Sheet.objects.get(id=sheet_id)
                    item_sheet_equipment.equipment_type = Equipment.objects.get(id=form.cleaned_data['equipment_type'].id)
                    item_sheet_equipment.save()
                return redirect('sheetEquipment', sheet_id)
    first_equipment = sheet_equipments.first()
    if first_equipment is None:
        first_equipment_id = ''
    else:
        first_equipment_id = first_equipment.id
    parameters = {'sheet': sheet,
                  'form': form,
                  'sheet_equipments': sheet_equipments,
                  'equipment_in': equipment_in,
                  'equipments_count': equipments_count,
                  'equipments': equipments,
                  'first_equipment_id': first_equipment_id,
                  }
    return render(request, "sheetEquipment.html", parameters)


@login_required
def equipments_list(request, sheet_id):
    my_sheet = Sheet.objects.get(id=sheet_id)
    sheet_equipments = SheetEquipment.objects.filter(sheet=sheet_id)

    parameters = {'sheet_equipments': sheet_equipments,
                  'my_sheet': my_sheet,
                  'sheet_id': sheet_id,
                  'WEB_URL': WEB_URL,
                  'MEDIA_URL': MEDIA_URL,
                  }
    return render(request, "sheetEquipmentsList.html", parameters)


def fetch_sheet_equipment_data(equipment: SheetEquipment):
    def get_object_or_none(queryset, *args, **kwargs):
        try:
            return queryset.get(*args, **kwargs)
        except queryset.model.DoesNotExist:
            return None

    def get_attribute_value(queryset, attribute_name, default_value, *args, **kwargs):
        obj = get_object_or_none(queryset, *args, **kwargs)
        if obj:
            field_object = queryset.model._meta.get_field(attribute_name)
            return field_object.value_from_object(obj)
        else:
            return default_value

    equipment_data = {}
    se_common_data_set = equipment.sheetequipmentcommondata_set
    e_custom_field_set = equipment.equipment.equipmentcustomfield_set
    se_actual_data_set = equipment.sheetequipmentactualdata_set
    data_fields = [
        (
            "get_attribute_value(se_common_data_set, 'value', '', key__column_title__iexact='{}')",
            [
                ('fan_no', 'fan no.'),
                ('location', 'location'),
                ('area_served', 'area served'),
            ]
        ),
        (
            "get_attribute_value(equipment.sheetequipmentcustomdata_set, 'value', '', key__column_title__iexact='{}')",
            [
                ('serial_no', 'Serial No.'),
                ('note', 'Note'),
            ]
        ),
        (
            "get_attribute_value(equipment.sheetequipmentcustomdata_set, 'value', '', key__column_title__iexact='{}')",
            [('df_cooling', 'DF Cooling'), ]
        ),
        (
            "get_attribute_value(equipment.sheetequipmentcustomdata_set, 'value', '', key__column_title__iexact='{}')",
            [('df_heating', 'DF Heating'), ]
        ),
        (
            "equipment.equipment.manufacturer",
            [('manufacturer', ''), ]
        ),
        (
            "equipment.equipment.model_number",
            [('model_no', ''), ]
        ),
        (
            """{{'design': get_attribute_value(e_custom_field_set, 'company_value', '', equipment_value_name__iexact='{0}'),
                'actual': get_attribute_value(se_actual_data_set, 'value', '', key__equipment_value_name__iexact='{0}')}}""",
            [
                ('total_cfm', 'Total C.F.M.'),
                ('return_air_cfm', 'Return Air C.F.M.'),
                ('outdoor_air_cfm', 'Outdoor Air C.F.M.'),
                ('total_sp_ext_sp', 'Total SP (Ext. SP)'),
                ('fan_unit_suction_pressure', 'Fan (Unit) Suction Pressure'),
                ('discharge_pressure_fan_unit', 'Discharge Pressure, Fan/Unit'),
                ('fan_rpm', 'Fan R.P.M'),
                ('hp', 'H.P.'),
                ('voltage', 'Voltage'),
                ('phase', 'Phase'),
                ('amperage', 'Amperage'),
                ('bhp_calc', 'B.H.P. (Calc.)'),
                ('frame', 'Frame'),
                ('sf_code', 'S.F. / Code'),
                ('motor_rpm', 'Motor RPM'),
            ]
        ),
    ]
    for field_value_str, items in data_fields:
        for key, name in items:
            equipment_data[key] = eval(field_value_str.format(name))

    for key in equipment_data:
        if key in ['df_cooling', 'df_heating']:
            if equipment_data[key]:
                equipment_data[key] = equipment_data[key] + '°'

    return equipment_data


def get_pdf_parameters(sheet_id, is_report_pdf):
    my_sheet = Sheet.objects.get(id=sheet_id)
    sheet_equipments = SheetEquipment.objects.filter(sheet=my_sheet, main_data_entry_completed=True,
                                                     design_data_entry_completed=True)
    if is_report_pdf:
        sheet_equipments = sheet_equipments.filter(actual_data_entry_completed=True)

    data = []
    len_equipments = sheet_equipments.count()
    equipment_in_page = 2
    for i in range(math.ceil(len_equipments / equipment_in_page)):
        page = []
        for j in range(equipment_in_page):
            index = i * equipment_in_page + j
            if index < len_equipments:
                page.append(fetch_sheet_equipment_data(sheet_equipments[index]))
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
            'data': data,
        },
        'file_name': ('TEST SHEET {}-{}{}'.format(my_sheet.project.proposal.quote.estimate.project.name,
                                                  my_sheet.project.project_number,
                                                  '' if is_report_pdf else ' TECH')).upper(),
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/airMovingEquipmentTechTemplate.html', parameters,
                                                  'airMovingEquipmentReport')
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
    pdf_name, pdf_path = PDFRender.render_to_file('pdfTemplates/airMovingEquipmentTemplate.html', parameters,
                                                  'airMovingEquipmentReport')

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + pdf_name
            return response
    else:
        return 'error'


@login_required
def sheet_equipment_common_data(request, sheet_equipment_id):
    sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    showing_fields = TestSheetColumn.objects.filter(test_sheet__name__icontains='air mov')
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=sheet_equipment.equipment_type).distinct()
    Equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='air mov', equipment_type=sheet_equipment.equipment_type)

    equipments = Equipment.objects.filter(test_sheet__name__icontains='air mov')

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', sheet_equipment.sheet.id)
        for every_field in showing_fields:
            key = every_field
            field_value = request.POST.get('showing_field_value_'+str(every_field.id))
            new_record = SheetEquipmentCommonData(sheet_equipment_id=sheet_equipment_id, key=key, value=field_value)
            new_record.save()
        new_update = SheetEquipment.objects.get(id=sheet_equipment_id)
        new_update.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
        new_update.main_data_entry_completed = True
        new_update.save()
        return redirect('sheetEquipmentsList', sheet_equipment.sheet.id)

    parameters = {'sheet_equipment': sheet_equipment,
                  'showing_fields': showing_fields,
                  'manufacturers': manufacturers,
                  'Equipment_db': Equipment_db,
                  }

    return render(request, "sheetEquipmentCommonData.html", parameters)


@login_required
def sheet_equipment_common_data_edit(request, sheet_equipment_id):
    this_sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    showing_fields = TestSheetColumn.objects.filter(test_sheet__name__icontains='air mov')
    value_fields = SheetEquipmentCommonData.objects.filter(sheet_equipment_id=sheet_equipment_id)
    manufacturers = EquipmentManufacturer.objects.filter(equipmentdb__equipment_type=this_sheet_equipment.equipment_type).distinct()
    Equipment_db = EquipmentDb.objects.filter(equipment_type__test_sheet__name__icontains='air mov', equipment_type=this_sheet_equipment.equipment_type)
    this_equipment = EquipmentDb.objects.get(id=this_sheet_equipment.equipment.id)

    equipments = Equipment.objects.filter(test_sheet__name__icontains=this_sheet_equipment)

    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            for value_field in value_fields:
                SheetEquipmentCommonData.objects.filter(key=value_field.key,
                                                        sheet_equipment=this_sheet_equipment).update(value=request.POST.get('showing_field_value_' + str(value_field.id)))
            this_sheet_equipment.equipment = EquipmentDb.objects.get(id=request.POST.get('id_equipment'))
            this_sheet_equipment.save()
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)

    parameters = {'this_sheet_equipment': this_sheet_equipment,
                  'showing_fields': showing_fields,
                  'manufacturers': manufacturers,
                  'value_fields': value_fields,
                  'Equipment_db': Equipment_db,
                  'this_equipment': this_equipment,
                  }

    return render(request, "sheetEquipmentCommonDataEdit.html", parameters)


@login_required
def review_equipment_values(request, sheet_equipment_id):
    this_sheet_equipment = get_object_or_404(SheetEquipment, id=sheet_equipment_id)
    this_equipment = this_sheet_equipment.equipment
    custom_fields = this_equipment.equipment_type.equipmenttypecustomfield_set.all()
    custom_operations = this_equipment.equipment_type.equipmenttypecustomoperation_set.all()
    show_parentheses_fields = list(map(lambda item:
                                       {'id': f'company_value_{item.id}', 'defaultValue': item.default_value, },
                                       custom_fields.filter(Q(show_parentheses=ShowParenthesesChoices.Design.value) |
                                                            Q(show_parentheses=ShowParenthesesChoices.Both.value))))
    required_fields = list(map(lambda item: f'company_value_{item.id}', custom_fields.filter(required_in_design=True)))
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            for custom_field in custom_fields:
                if custom_field.field_range_or_selective == FieldRangeOrSelectiveChoices.Range.value:
                    if custom_field.field_type == FieldTypeChoices.Characters.value:
                        break
                    my_range = custom_field.field_range.split('-')
                    min_value = my_range[0]
                    max_value = my_range[1]
                    sent_value = request.POST.get('company_value_' + str(custom_field.id))
                    if custom_field.field_type == FieldTypeChoices.Integer.value:
                        sent_value = int(sent_value)
                        min_value = int(min_value)
                        max_value = int(max_value)
                    elif custom_field.field_type == FieldTypeChoices.Float.value:
                        sent_value = float(sent_value)
                        min_value = float(min_value)
                        max_value = float(max_value)
                    if sent_value < min_value or sent_value > max_value:
                        error_msg = custom_field.field_name + " Value is not in Range!"
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_field.field_range_or_selective == FieldRangeOrSelectiveChoices.Selective.value:
                    if custom_field.field_type == FieldTypeChoices.Characters.value:
                        break
                    my_range = custom_field.field_range.split(',')
                    sent_value = request.POST.get('company_value_' + str(custom_field.id))
                    is_in_my_range = 0
                    for number in my_range:
                        if custom_field.field_type == FieldTypeChoices.Integer.value:
                            if int(number) == int(sent_value):
                                is_in_my_range = 1
                        elif custom_field.field_type == FieldTypeChoices.Float.value:
                            if float(number) == float(sent_value):
                                is_in_my_range = 1
                    if is_in_my_range == 0:
                        error_msg = custom_field.field_name + " Value is not selected right!"
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
            for custom_operation in custom_operations:
                this_operation = str(custom_operation.operation)
                this_result = str(custom_operation.result_field)
                operation_msg = str(custom_operation.operation)
                result_msg = str(custom_operation.result_field)
                for custom_field in custom_fields:
                    this_operation = this_operation.replace('[field-' + str(custom_field.id) + ']',
                                                            request.POST.get('company_value_' + str(custom_field.id)))
                    this_result = this_result.replace('[field-' + str(custom_field.id) + ']',
                                                      request.POST.get('company_value_' + str(custom_field.id)))
                    operation_msg = operation_msg.replace('[field-' + str(custom_field.id) + ']', custom_field.field_name)
                    result_msg = result_msg.replace('[field-' + str(custom_field.id) + ']', custom_field.field_name)
                if custom_operation.operand_type == OperandChoices.EqualTo.value:
                    if eval(this_operation) != eval(this_result):
                        error_msg = operation_msg + " must be equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == OperandChoices.GreaterThan.value:
                    if eval(this_operation) <= eval(this_result):
                        error_msg = operation_msg + " must be greater than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == OperandChoices.GreaterOrEqualTo.value:
                    if eval(this_operation) < eval(this_result):
                        error_msg = operation_msg + " must be greater than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == OperandChoices.SmallerThan.value:
                    if eval(this_operation) >= eval(this_result):
                        error_msg = operation_msg + " must be smaller than " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)
                elif custom_operation.operand_type == OperandChoices.SmallerOrEqualTo.value:
                    if eval(this_operation) > eval(this_result):
                        error_msg = operation_msg + " must be smaller than or equal to " + result_msg
                        parameters = {'this_equipment': this_equipment,
                                      'this_sheet_equipment': this_sheet_equipment,
                                      'custom_fields': custom_fields,
                                      'show_parentheses_fields': show_parentheses_fields,
                                      'error_msg': error_msg,
                                      'required_fields': required_fields,
                                      }
                        return render(request, "EquipmentDesignValue.html", parameters)

            for custom_field in custom_fields:
                new_value = request.POST.get('company_value_' + str(custom_field.id)).strip()
                if not new_value:
                    new_value = custom_field.default_value.strip()

                num_results = EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                                  equipment=this_equipment).count()
                if num_results > 0:
                    EquipmentCustomField.objects.filter(equipment_value_name=custom_field.field_name,
                                                        equipment=this_equipment.id).update(company_value=new_value)
                else:
                    new_object = EquipmentCustomField(equipment_value_name=custom_field.field_name, company_value=new_value, equipment=this_equipment)
                    new_object.save()
            this_sheet_equipment.design_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
    parameters = {'this_equipment': this_equipment,
                  'this_sheet_equipment': this_sheet_equipment,
                  'custom_fields': custom_fields,
                  'show_parentheses_fields': show_parentheses_fields,
                  'required_fields': required_fields,
                  }
    return render(request, "EquipmentDesignValue.html", parameters)


def check_actual_values(request, this_sheet_equipment, equipment_type_custom_fields, custom_fields, insert=True):
    actual_data_custom_operations = this_sheet_equipment.equipment.equipment_type.actualdatacustomoperation_set \
        .filter(~Q(operand_type=OperandChoices.AssignTo.value))
    conv_to_num = None

    for equipment_type_custom_field in equipment_type_custom_fields:
        if equipment_type_custom_field.field_type == FieldTypeChoices.Characters.value:
            continue
        elif equipment_type_custom_field.field_type == FieldTypeChoices.Integer.value:
            conv_to_num = int
        elif equipment_type_custom_field.field_type == FieldTypeChoices.Float.value:
            conv_to_num = float

        field_name = equipment_type_custom_field.field_name
        if insert:
            related_id = custom_fields.get(equipment_value_name=field_name).id
        else:
            related_id = custom_fields.get(key__equipment_value_name=field_name).id

        try:
            sent_value = conv_to_num(request.POST.get('actual_value_' + str(related_id)))
        except ValueError:
            return "{} value is not valid. The value must be {} number.".format(
                field_name, 'integer' if conv_to_num == int else 'float')

        if equipment_type_custom_field.field_range_or_selective == FieldRangeOrSelectiveChoices.Range.value:
            my_range = equipment_type_custom_field.field_range.split('-')
            min_value = conv_to_num(my_range[0])
            max_value = conv_to_num(my_range[1])
            if sent_value < min_value or max_value < sent_value:
                return "{} value is not in range. Valid range is {}.".format(field_name,
                                                                             equipment_type_custom_field.field_range)
        elif equipment_type_custom_field.field_range_or_selective == FieldRangeOrSelectiveChoices.Selective.value:
            my_range = equipment_type_custom_field.field_range.split(',')
            if sent_value not in map(lambda x: conv_to_num(x), my_range):
                return "{} value is not selected right. Valid choices are {}.".format(
                    field_name, equipment_type_custom_field.field_range)

    for custom_operation in actual_data_custom_operations:
        left_side = left_side_msg = str(custom_operation.operation)
        right_side = right_side_msg = str(custom_operation.result_field)

        for equipment_type_custom_field in equipment_type_custom_fields:
            field_name = equipment_type_custom_field.field_name
            if insert:
                design_value = custom_fields.get(equipment_value_name=field_name)
                related_id = design_value.id
            else:
                actual_value = custom_fields.get(key__equipment_value_name=field_name)
                related_id = actual_value.id
                design_value = actual_value.key
            if '-' in design_value.company_value:
                spliced_design_values = design_value.company_value.replace(' ', '').split('-')
                correct_design_value = min(spliced_design_values, key=lambda x: abs(float(x)-eval(request.POST.get('actual_value_' + str(related_id)))))
            else:
                correct_design_value = design_value.company_value
            fields = [
                ('[field-{}-design]'.format(equipment_type_custom_field.id), correct_design_value),
                ('[field-{}-actual]'.format(equipment_type_custom_field.id), request.POST.get('actual_value_' + str(related_id))),
            ]
            for name, value in fields:
                left_side = left_side.replace(name, value)
                right_side = right_side.replace(name, value)
                left_side_msg = left_side_msg.replace(name, field_name)
                right_side_msg = right_side_msg.replace(name, field_name)

        left_side = eval(left_side)
        right_side = eval(right_side)
        if custom_operation.operand_type == OperandChoices.EqualTo.value:
            if left_side != right_side:
                return left_side_msg + " must be equal to " + right_side_msg
        elif custom_operation.operand_type == OperandChoices.GreaterThan.value:
            if left_side <= right_side:
                return left_side_msg + " must be greater than " + right_side_msg
        elif custom_operation.operand_type == OperandChoices.GreaterOrEqualTo.value:
            if left_side < right_side:
                return left_side_msg + " must be greater than or equal to " + right_side_msg
        elif custom_operation.operand_type == OperandChoices.SmallerThan.value:
            if left_side >= right_side:
                return left_side_msg + " must be smaller than " + right_side_msg
        elif custom_operation.operand_type == OperandChoices.SmallerOrEqualTo.value:
            if left_side > right_side:
                return left_side_msg + " must be smaller than or equal to " + right_side_msg

    return None


def parse_assigment_operations_actual(this_sheet_equipment, equipment_type_custom_fields, custom_fields, insert=True):
    assignment_operations = this_sheet_equipment.equipment.equipment_type.actualdatacustomoperation_set \
        .filter(operand_type=OperandChoices.AssignTo.value)
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
                related_value = '{' + str(custom_field.id) + ',' + related_value + '}'
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


def get_required_fields_actual(equipment_type_custom_fields, custom_fields, insert=True):
    required_fields = equipment_type_custom_fields.filter(required_in_actual=True)
    if insert:
        fields = map(lambda item: f'actual_value_{custom_fields.get(equipment_value_name=item.field_name).id}',
                     required_fields)
    else:
        fields = map(lambda item: f'actual_value_{custom_fields.get(key__equipment_value_name=item.field_name).id}',
                     required_fields)
    return list(fields)


@login_required
def equipment_actual_values(request, sheet_equipment_id):
    this_sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    equipment_type_custom_fields = this_sheet_equipment.equipment.equipment_type.equipmenttypecustomfield_set.all()
    other_custom_fields = SheetActualDataCustomField.objects.filter(test_sheet__name__icontains='air mov')
    custom_fields = EquipmentCustomField.objects.filter(equipment=this_sheet_equipment.equipment)
    assignment_operations = parse_assigment_operations_actual(this_sheet_equipment, equipment_type_custom_fields,
                                                              custom_fields)
    show_parentheses_fields = get_show_parentheses_fields_actual(equipment_type_custom_fields, custom_fields)
    required_fields = get_required_fields_actual(equipment_type_custom_fields, custom_fields)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            error_msg = check_actual_values(request, this_sheet_equipment, equipment_type_custom_fields, custom_fields)
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'custom_fields': custom_fields,
                    'other_custom_fields': other_custom_fields,
                    'assignment_operations': assignment_operations,
                    'show_parentheses_fields': show_parentheses_fields,
                    'error_msg': error_msg,
                    'required_fields': required_fields,
                }
                return render(request, "EquipmentActualValue.html", parameters)

            for other_custom_field in other_custom_fields:
                new_object = SheetEquipmentCustomData(key=other_custom_field, value=request.POST.get(
                    'other_value_' + str(other_custom_field.id)), sheet_equipment=this_sheet_equipment)
                new_object.save()
            for custom_field in custom_fields:
                new_value = request.POST.get('actual_value_' + str(custom_field.id)).strip()
                if not new_value:
                    new_value = equipment_type_custom_fields.get(
                        field_name=custom_field.equipment_value_name).default_value.strip()

                num_results = SheetEquipmentActualData.objects.filter(
                    key__equipment_value_name=custom_field.equipment_value_name,
                    sheet_equipment=this_sheet_equipment).count()

                if num_results > 0:
                    SheetEquipmentActualData.objects.filter(key__equipment_value_name=custom_field.equipment_value_name,
                                                            sheet_equipment=this_sheet_equipment).update(value=new_value)
                else:
                    new_object_key = EquipmentCustomField.objects.get(equipment=this_sheet_equipment.equipment, equipment_value_name=custom_field.equipment_value_name)
                    new_object = SheetEquipmentActualData(key=new_object_key, value=new_value, sheet_equipment=this_sheet_equipment)
                    new_object.save()
            this_sheet_equipment.actual_data_entry_completed = True
            this_sheet_equipment.save()
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
    parameters = {'this_sheet_equipment': this_sheet_equipment,
                  'custom_fields': custom_fields,
                  'other_custom_fields': other_custom_fields,
                  'assignment_operations': assignment_operations,
                  'show_parentheses_fields': show_parentheses_fields,
                  'required_fields': required_fields,
                  }
    return render(request, "EquipmentActualValue.html", parameters)


@login_required
def equipment_actual_values_edit(request, sheet_equipment_id):
    this_sheet_equipment = SheetEquipment.objects.get(id=sheet_equipment_id)
    equipment_type_custom_fields = this_sheet_equipment.equipment.equipment_type.equipmenttypecustomfield_set.all()
    other_custom_fields = SheetEquipmentCustomData.objects.filter(sheet_equipment=this_sheet_equipment)
    custom_fields = SheetEquipmentActualData.objects.filter(sheet_equipment=this_sheet_equipment)
    assignment_operations = parse_assigment_operations_actual(this_sheet_equipment, equipment_type_custom_fields,
                                                              custom_fields, False)
    show_parentheses_fields = get_show_parentheses_fields_actual(equipment_type_custom_fields, custom_fields, False)
    required_fields = get_required_fields_actual(equipment_type_custom_fields, custom_fields, False)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
        if request.POST.get("next"):
            error_msg = check_actual_values(request, this_sheet_equipment, equipment_type_custom_fields, custom_fields,
                                            False)
            if error_msg is not None:
                parameters = {
                    'this_sheet_equipment': this_sheet_equipment,
                    'custom_fields': custom_fields,
                    'other_custom_fields': other_custom_fields,
                    'assignment_operations': assignment_operations,
                    'show_parentheses_fields': show_parentheses_fields,
                    'error_msg': error_msg,
                    'required_fields': required_fields,
                }
                return render(request, "EquipmentActualValueEdit.html", parameters)

            for other_custom_field in other_custom_fields:
                SheetEquipmentCustomData.objects.filter(key=other_custom_field.key,
                                                        sheet_equipment=this_sheet_equipment).update(
                    value=request.POST.get('other_value_' + str(other_custom_field.id)))
            for custom_field in custom_fields:
                new_value = request.POST.get('actual_value_' + str(custom_field.id)).strip()
                if not new_value:
                    new_value = equipment_type_custom_fields.get(
                        field_name=custom_field.key.equipment_value_name).default_value.strip()

                SheetEquipmentActualData.objects.filter(key=custom_field.key,
                                                        sheet_equipment=this_sheet_equipment).update(value=new_value)
            return redirect('sheetEquipmentsList', this_sheet_equipment.sheet.id)
    parameters = {'this_sheet_equipment': this_sheet_equipment,
                  'custom_fields': custom_fields,
                  'other_custom_fields': other_custom_fields,
                  'assignment_operations': assignment_operations,
                  'show_parentheses_fields': show_parentheses_fields,
                  'required_fields': required_fields,
                  }
    return render(request, "EquipmentActualValueEdit.html", parameters)


@login_required
def sheet_delete(request, sheet_id):
    this_sheet = get_object_or_404(Sheet, id=sheet_id)
    if request.method == 'POST':
        if request.POST.get("cancel"):
            return redirect('sheetHome')
        if request.POST.get("confirm"):
            this_sheet.delete()
            return redirect('sheetHome')
    parameters = {'this_sheet': this_sheet,
                  }
    return render(request, "sheet_delete.html", parameters)


@login_required
def sheet_equipment_delete(request, sheet_id, sheet_equipment_name):
    this_sheet = SheetEquipment.objects.filter(equipment_type__name__iexact=sheet_equipment_name, sheet=sheet_id)
    if request.POST.get("confirm"):
        this_sheet.delete()
        return redirect('sheetEquipment', sheet_id)
    if request.POST.get("cancel"):
        return redirect('sheetEquipment', sheet_id)
    parameters = {'this_sheet': this_sheet,
                  'sheet_equipment_name': sheet_equipment_name,
                  }
    return render(request, "sheet_delete.html", parameters)
