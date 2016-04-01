# Django Imports
from django import template
from django.utils.safestring import mark_safe

# WaW Imports
from wawmembers import utilities

'''
Text manipulation for the military policies page.
'''

register = template.Library()

def trsort(inhome, instaging):
    'Chooses the best training to present.'
    home = inhome[0]
    staging = instaging[0]
    wlist = ['F','W','C','D','R']
    if (home == 'W' and staging in wlist[:1]) or (home == 'C' and staging in wlist[:2]) \
      or (home == 'D' and staging in wlist[:3]) or (home == 'R' and staging in wlist[:4]):
        return instaging
    else:
        return inhome


def hyphenate(ownlist, otherlist=None):
    if otherlist != None:
        # no ships, no freighters, no flagship
        if sum(ownlist[2:11]) == 0 and ownlist[15] == 0 and ownlist[17] == False and \
          sum(otherlist[2:11]) == 0 and otherlist[15] == 0 and otherlist[17] == False:
            return True
        else:
            return False
    else:
        if sum(ownlist[2:11]) == 0 and ownlist[15] == 0 and ownlist[17] == False:
            return True
        else:
            return False


def hyphendisplay(value, ownlist, otherlist=None):
    if hyphenate(ownlist, otherlist):
        return '-'
    else:
        return value

register.simple_tag(hyphendisplay)


def wearinessdisplay(homelist, staginglist):
    toreturn = '<td class="center">%s</td><td class="center">%s</td>'
    if hyphenate(homelist) and hyphenate(staginglist):
        return toreturn % ('-','-')
    elif hyphenate(homelist):
        return toreturn % ('-',homelist[12])
    elif hyphenate(staginglist):
        return toreturn % (homelist[12],'-')
    else:
        return '<td class="center" colspan="2">%s</td>' % homelist[12]

register.simple_tag(wearinessdisplay)


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


def supplydisplay(value, ownlist):
    value = hyphendisplay(value, ownlist)
    fuel = ownlist[13]

    if value != '-':
        if 200*value > fuel:
            toreturn = '<span style="color:green;">%s</span>' % value
        else:
            toreturn = '<span style="color:red;">%s</span>' % value
    else:
        toreturn = '-'

    return mark_safe(toreturn)

register.simple_tag(supplydisplay)


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
