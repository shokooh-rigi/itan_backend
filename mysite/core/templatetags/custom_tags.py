from django import template
from ...settings import MEDIA_URL

register = template.Library()


@register.filter
def in_setting(things, key):
    return things.filter(key=key)


@register.simple_tag
def media_url():
    return MEDIA_URL
