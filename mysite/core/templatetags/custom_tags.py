from django import template
from mysite.dbmanagement.models import EquipmentTypeCustomField, EquipmentCustomField
from ...settings import MEDIA_URL
from django.shortcuts import get_object_or_404


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
