from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Look up `key` in a plain dict from a template, where `d[key]` syntax
    isn't available. Used to match a checklist master item to its saved
    result row (keyed by item id) in inspections/workspace.html."""
    if d is None:
        return None
    return d.get(key)
