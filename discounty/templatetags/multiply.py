from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value+(value*arg/100)

@register.filter
def multiply_default(value, arg):
    return value * arg