# Django Imports
from django import template
from django.utils.safestring import mark_safe

# WaW Imports
from wawmembers import utilities

'''
Text manipulation for the military policies page.
'''

register = template.Library()



def combobasepower(homelist, staginglist, target):
    home = utilities.militarypower(target, target.region)
    staging = utilities.militarypower(target, 'S')
    if hyphenate(homelist) and hyphenate(staginglist):
        return '-'
    else:
        return home + staging

register.simple_tag(combobasepower)


def combotraining(homelist, staginglist):
    if hyphenate(homelist):
        return staginglist[11]
    elif hyphenate(staginglist):
        return homelist[11]
    elif hyphenate(homelist) and hyphenate(staginglist):
        return '-'
    else:
        return trsort(homelist[11], staginglist[11])

register.simple_tag(combotraining)


def powerdisplay(value, ownlist):
    value = hyphendisplay(value, ownlist)
    power = ownlist[14]
    pwf = ownlist[16]

    if value != '-':
        if pwf == power:
            toreturn = value
        else:
            toreturn = '<span style="color:red;">%s</span>' % value
    else:
        toreturn = '-'

    return mark_safe(toreturn)

register.simple_tag(powerdisplay)
