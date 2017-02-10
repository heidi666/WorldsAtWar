# Django Imports
from django import template
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.utils import ErrorDict
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

# WaW Imports
from wawmembers.models import World

'''
Simple text manipulation filters.
'''

register = template.Library()

ntsdict = {'0':'a','1':'b','2':'c','3':'d','4':'e','5':'f','6':'g','7':'h','8':'i','9':'i'}

def lookup(d, key):
    return d[key]

register.filter('lookup', lookup)


def repeat(string, times):
    return string*times

register.filter('repeat', repeat)


def nice_errors(form, non_field_msg='General form errors'):
    nice_errors = ErrorDict()
    if isinstance(form, forms.BaseForm):
        for field, errors in form.errors.items():
            if field == NON_FIELD_ERRORS:
                key = non_field_msg
            else:
                key = form.fields[field].label
            nice_errors[key] = errors
    return nice_errors

register.filter('nice_errors', nice_errors)


def notostring(number):
    string = ''
    for char in str(number):
        string += ntsdict[char]
    return string

register.filter('notostring', notostring)


def tradesleft(amount):
    plural = ('is' if amount == 1 else 'are')
    return 'There %s %s of this trade remaining.' % (plural, amount)

register.filter('tradesleft', tradesleft)


def linebreaks(string, times):
    temp = string.replace('<','').replace('>','')
    templist = temp.split('[br]', times)
    toreturn = '<br>'.join(templist)
    return mark_safe(toreturn)

register.filter('linebreaks', linebreaks)


def worldlink(world):
    return mark_safe('<a href="%s">%s</a>' % (world.get_absolute_url(), world.name))

register.filter('worldlink', worldlink)


def formlookup(form, key):
    return form[key]

register.filter('formlookup', formlookup)
