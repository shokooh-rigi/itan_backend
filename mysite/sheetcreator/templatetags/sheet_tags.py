from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField, FieldTypeChoices, DataTypeChoices
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404

from mysite.sheetcreator.models import *

register = template.Library()


@register.simple_tag
def get_design_value(request, design_field, equipment, request_page):
    print(design_field, ' | ', equipment)
    if request_page == 1:
        return_value = EquipmentDbDesignData.objects.filter(equipment=equipment, key=design_field)
        if return_value.exists():
            return EquipmentDbDesignData.objects.get(equipment=equipment, key=design_field).value
        else:
            return TestSheetField.objects.get(id=design_field.id).default_value
    elif request_page == 2:
        if request.method == 'POST':
            return request.POST.get(f'company_value_{design_field.id}')
        return_value = TestSheetData.objects.filter(data_type=DataTypeChoices.Design.value, sheet_equipment=equipment,
                                                    sheet_field=design_field)
        if return_value.count() > 0:
            return return_value.first().value
        else:
            if equipment.equipment:
                return_value = EquipmentDbDesignData.objects.filter(equipment=equipment.equipment, key=design_field)
                if return_value.exists():
                    return return_value.first().value
            else:
                this_sheet_field = get_object_or_404(TestSheetField, id=design_field.id)
                return this_sheet_field.default_value


@register.simple_tag
def get_terminal_design_value(request, design_field, air_terminal_equipment):
    terminal_equipment = AirTerminalEquipment.objects.get(id=air_terminal_equipment)
    return_value = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Design.value,
                                                       air_terminal_equipment=terminal_equipment,
                                                       sheet_field=design_field)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=design_field.id)
        return this_sheet_field.default_value


@register.simple_tag
def get_terminal_actual_value(request, actual_field, air_terminal_equipment):
    terminal_equipment = AirTerminalEquipment.objects.get(id=air_terminal_equipment)
    return_value = AirTerminalSheetData.objects.filter(data_type=DataTypeChoices.Actual.value,
                                                       air_terminal_equipment=terminal_equipment,
                                                       sheet_field=actual_field)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=actual_field.id)
        return this_sheet_field.default_value


@register.simple_tag
def get_terminal_code_value(request, air_terminal_equipment):
    terminal_equipment_count = AirTerminalEquipment.objects.filter(id=air_terminal_equipment).count()
    if terminal_equipment_count > 0:
        terminal_equipment = AirTerminalEquipment.objects.get(id=air_terminal_equipment).code
        if terminal_equipment:
            return terminal_equipment.id
        else:
            return ''
    else:
        return ''


@register.simple_tag
def get_actual_value(request, actual_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'actual_value_{actual_field.id}')
    return_value = TestSheetData.objects.filter(data_type=DataTypeChoices.Actual.value, sheet_equipment=equipment,
                                                sheet_field=actual_field)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=actual_field.id)
        return this_sheet_field.default_value


@register.simple_tag
def get_field_type(field):
    field_type = field.field_type

    if field_type == FieldTypeChoices.Integer.value:
        return 'type=number'
    elif field_type == FieldTypeChoices.Float.value:
        return 'type=number step=any'
    elif field_type == FieldTypeChoices.SelectOption.value:
        return 'type=checkbox'
    return 'type=text'


@register.filter()
def concatenate(value, arg):
    """concatenate the value and the arg."""
    try:
        return str(value) + str(arg)
    except Exception:
        return ''


@register.filter
def normalize_string(value):
    return value.replace(" ", "_").replace(".", "").replace("(", "").replace(")", "")
