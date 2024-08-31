from django import template

register = template.Library()

@register.filter
def add_prefix(value, prefix):
    return f"{prefix}{value}"

@register.filter
def fill_dots(value, total_length=80):
    if not isinstance(value, str):
        return value
    
    # Number of characters taken by the title and one space before dots
    title_length = len(value) + 1
    
    # Calculate the remaining space for dots
    remaining_length = int(total_length) - title_length
    
    # Generate the appropriate number of dots
    if remaining_length > 0:
        dots = '.' * remaining_length
        return f"{value} {dots}"
    else:
        # If the title is too long, just return the title with no dots
        return value
