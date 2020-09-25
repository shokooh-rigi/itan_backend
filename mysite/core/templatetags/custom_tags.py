from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField, FieldTypeChoices
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404

from mysite.sheetcreator.models import SheetEquipmentActualData


register = template.Library()


@register.filter
def in_setting(things, key):
    return things.filter(key=key)


@register.simple_tag
def media_url():
    return MEDIA_URL


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='split')
def split(value):
    return value.split('-')


@register.simple_tag
def get_post_variable(request, cfi, equipment):
    if request.POST:
        answer = request.POST.get('company_value_' + str(cfi.id))
        return answer
    else:
        num_results = EquipmentCustomField.objects.filter(equipment_value_name=cfi.field_name, equipment=equipment.id).count()
        if num_results > 0:
            this_equipment = get_object_or_404(EquipmentCustomField, equipment_value_name=cfi.field_name, equipment=equipment.id)
            return this_equipment.company_value
        else:
            this_equipment_type = get_object_or_404(EquipmentTypeCustomField, id=cfi.id)
            return this_equipment_type.default_value


@register.simple_tag
def get_value_from_post(request, default_value, *variable_name):
    if request.POST:
        return request.POST.get(''.join(map(lambda x: str(x), variable_name)))
    else:
        if type(default_value) == EquipmentCustomField:
            return default_value.equipment.equipment_type.equipmenttypecustomfield_set.get(
                field_name=default_value.equipment_value_name).default_value
        return default_value


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

    if field_type == FieldTypeChoices.Integer.value or field_type == FieldTypeChoices.Float.value:
        return 'number'
    return 'text'
