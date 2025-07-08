from django import template
from django.forms import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    # Check if the input is a Django form field
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    # If not, return the field as is
    return field

@register.filter(name='mul')
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except:
        return 0

@register.filter(name='div')
def div(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except:
        return 0