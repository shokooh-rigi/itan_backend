from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField, FieldTypeChoices, DataTypeChoices
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404

from ..models import *

register = template.Library()


@register.simple_tag
def get_induction_unit_design_value(request, design_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'design_value_{design_field.id}')
    return_value = InductionUnitSheetData.objects.filter(induction_unit_equipment=equipment, sheet_field=design_field, data_type=1)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=design_field.id)
        return this_sheet_field.default_value


@register.simple_tag
def get_induction_unit_actual_value(request, actual_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'actual_value_{actual_field.id}')
    return_value = InductionUnitSheetData.objects.filter(induction_unit_equipment=equipment, sheet_field=actual_field, data_type=2)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=actual_field.id)
        return this_sheet_field.default_value
