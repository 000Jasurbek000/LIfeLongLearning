from django import template
from django.utils.safestring import mark_safe

from pages.i18n import get_language, translate

register = template.Library()


@register.simple_tag(takes_context=True)
def t(context, key, fallback=None):
    request = context.get('request')
    language_code = get_language(request)
    return mark_safe(translate(key, language_code, fallback))
