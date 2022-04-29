from django import template
from django.shortcuts import get_object_or_404

from ..models import *

register = template.Library()


@register.simple_tag
def get_air_moving_equipment_design_value(request, design_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'design_value_{design_field.id}')
    if AirMovingEquipmentEquipment.objects.get(id=equipment.id).equipment:
        if EquipmentDbDesignData.objects.filter(equipment=equipment.equipment.id, key=design_field.id).exists():
            return EquipmentDbDesignData.objects.get(equipment=equipment.equipment.id, key=design_field.id).value
        else:
            return ''
    else:
        return_value = AirMovingEquipmentSheetData.objects.filter(data_type=1, air_moving_equipment_equipment=equipment, sheet_field=design_field)
        if return_value.count() > 0:
            return return_value.first().value
        else:
            this_sheet_field = get_object_or_404(TestSheetField, id=design_field.id)
            return this_sheet_field.default_value


@register.simple_tag
def get_air_moving_equipment_actual_value(request, actual_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'actual_value_{actual_field.id}')
    return_value = AirMovingEquipmentSheetData.objects.filter(data_type=2, air_moving_equipment_equipment=equipment, sheet_field=actual_field)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=actual_field.id)
        return this_sheet_field.default_value
