from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField, FieldTypeChoices
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404

from mysite.sheetcreator.models import SheetEquipmentActualData, TestSheetData, TestSheetField, EquipmentDbDesignData

register = template.Library()


@register.simple_tag
def get_design_value(request, design_field, equipment, request_page):
    if request_page == 1:
        return_value = EquipmentDbDesignData.objects.filter(equipment=equipment, key=design_field)
        if return_value.exists():
            return EquipmentDbDesignData.objects.get(equipment=equipment, key=design_field).value
        else:
            return TestSheetField.objects.get(id=design_field.id).default_value
    elif request_page == 2:
        if request.POST:
            answer = request.POST.get('company_value_' + str(design_field.id))
            return answer
        else:
            if equipment.equipment:
                return_value = EquipmentDbDesignData.objects.filter(equipment=equipment.equipment, key=design_field)
                if return_value.exists():
                    return EquipmentDbDesignData.objects.get(equipment=equipment.equipment, key=design_field).value
            else:
                num_results = TestSheetData.objects.filter(data_type=1, sheet_equipment=equipment, sheet_field=design_field).count()
                if num_results > 0:
                    this_field_value = TestSheetData.objects.filter(data_type=1, sheet_equipment=equipment, sheet_field=design_field)
                    return this_field_value.value
                else:
                    this_sheet_field = get_object_or_404(TestSheetField, id=design_field.id)
                    return this_sheet_field.default_value


@register.simple_tag
def get_field_type(field):
    field_type = 0
    if type(field) == EquipmentCustomField:
        field_type = field.equipment.equipment_type.equipmenttypecustomfield_set.get(
            field_name=field.equipment_value_name).field_type
    elif type(field) == SheetEquipmentActualData:
        field_type = field.key.equipment.equipment_type.equipmenttypecustomfield_set.get(
            field_name=field.key.equipment_value_name).field_type
    elif type(field) == EquipmentTypeCustomField:
        field_type = field.field_type

    if field_type == FieldTypeChoices.Integer.value:
        return 'type=number'
    elif field_type == FieldTypeChoices.Float.value:
        return 'type=number step=any'
    return 'type=text'


@register.filter()
def concatenate(value, arg):
    """concatenate the value and the arg."""
    try:
        return str(value) + str(arg)
    except Exception:
        return ''
