from django import template
from ..forms import *

register = template.Library()


@register.simple_tag
def submittal_number_generator(submittal_id):
    submittal = CompanySubmittal.objects.get(id=submittal_id)
    submittal_long_id = submittal.created_by.id + 100
    submittal_date_created = str(submittal.created_on).replace('-', '')[2:8]
    return submittal_date_created + str(submittal_long_id) + str(submittal.id).zfill(3)

