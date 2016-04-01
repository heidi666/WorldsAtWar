# Django Imports
from django import template
from django.utils.safestring import mark_safe

# WaW Imports
from wawmembers.models import Spy
import wawmembers.variables as v
import wawmembers.utilities as utilities

register = template.Library()

'''
Notifies when a spy can next take an action.
'''

def nextspyaction(spy):

    if spy.nextaction > v.now():
        timediff = spy.nextaction - v.now()
        hours, minutes, seconds = utilities.timedeltadivide(timediff)
        timetonextaction = '%s:%s:%s until your next spy action.' % (hours, minutes, seconds)
    else:
        timetonextaction = '<span style="color:green;">Your spy is available for actions.</span>'

    return mark_safe(timetonextaction)


register.simple_tag(nextspyaction)
