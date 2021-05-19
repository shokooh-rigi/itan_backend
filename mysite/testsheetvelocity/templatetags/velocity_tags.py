from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField, FieldTypeChoices, DataTypeChoices
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404

from ..models import VelocitySheetData, VelocitySheetTableData, TestSheetField

register = template.Library()


@register.simple_tag
def get_velocity_actual_value(request, actual_field, equipment):
    if request.method == 'POST':
        return request.POST.get(f'actual_value_{actual_field.id}')
    return_value = VelocitySheetData.objects.filter(velocity_equipment=equipment, sheet_field=actual_field)
    if return_value.count() > 0:
        return return_value.first().value
    else:
        this_sheet_field = get_object_or_404(TestSheetField, id=actual_field.id)
        return this_sheet_field.default_value


@register.simple_tag
def get_velocity_table_value(request, equipment):
    table_datas = VelocitySheetTableData.objects.filter(velocity_equipment=equipment)
    if table_datas.count() > 0:
        return_value = []
        row_num = 0
        row_data = []
        for table_data in table_datas:
            if table_data.row == row_num:
                row_data.append(int(table_data.value))
            else:
                return_value.append(row_data)
                row_num = table_data.row
                row_data = []
                row_data.append(int(table_data.value))
        return_value.append(row_data)
        return return_value
    else:
        return '{}'


@register.filter
def normalize_string(value):
    return value.replace(" ", "_").replace(".", "")


@register.simple_tag
def get_velocity_cell_value(equipment_id, row, col):
    exists = VelocitySheetTableData.objects.filter(velocity_equipment_id=equipment_id, row=row, col=col).count()
    if exists > 0:
        table_cell = VelocitySheetTableData.objects.get(velocity_equipment_id=equipment_id, row=row, col=col)
        return table_cell.value
    else:
        return ''

