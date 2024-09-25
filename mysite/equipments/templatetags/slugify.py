from django import template
import re

register = template.Library()

@register.filter
def slugify(value):
    """
    Converts a string to a slug suitable for use in URLs or HTML IDs.
    """
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = value.strip('-')
    return value
