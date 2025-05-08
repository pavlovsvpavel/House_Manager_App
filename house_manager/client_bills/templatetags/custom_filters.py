from django import template

register = template.Library()

@register.filter
def add(value1, value2):
    if value1 is None:
        value1 = 0
    if value2 is None:
        value2 = 0
    return value1 + value2