from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """Get an attribute from an object using a string name"""
    return getattr(obj, attr_name, None) 