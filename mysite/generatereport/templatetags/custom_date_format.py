from django import template
from datetime import datetime

register = template.Library()

@register.filter
def custom_date_format(value):
    if value:
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d")
            return date_obj.strftime("%m/%d/%Y")
        except ValueError:
            return value  # Return the original value if it's not a valid date format
    return ""
