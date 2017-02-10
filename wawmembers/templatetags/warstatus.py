# Django Imports
from django import template
from django.utils.safestring import mark_safe
# Django Imports
from django.templatetags.static import static

# Python Imports
import datetime as time

# WaW Imports
from wawmembers.models import World, War
import wawmembers.variables as v
import wawmembers.utilities as utilities

'''
War status for the galatic search.
'''

register = template.Library()

def warok(title):
    url = static('wawmembers/warok.png')
    return '<img src="%s" alt="warok" title="%s">' % (url, title)

def warnotok(title):
    url = static('wawmembers/warnotok.png')
    return '<img src="%s" alt="warnotok" title="%s">' % (url, title)

def warwarning(title):
    url = static('wawmembers/warwarning.png')
    return '<img src="%s" alt="warwarning" title="%s">' % (url, title)

def warstatus(world, target):
    try:
        War.objects.get(attacker=world, defender=target)
        atwar = True
    except:
        try:
            War.objects.get(attacker=target, defender=world)
            atwar = True
        except:
            atwar = False

    ownpower = targetpower = 0
    powerok = False
    for sector in v.sectors:
        for f in world.fleets.all().filter(sector=sector):
            ownpower += f.powermodifiers()
        for f in target.fleets.all().filter(sector=sector):
            targetpower += f.powermodifiers()
        if ownpower < 0.1*targetpower:
            powerok = True
            break
        ownpower = targetpower = 0

    if world == target:
        status = warnotok('You cannot declare war on yourself.')
    elif target.preferences.vacation:
        status = warnotok('This world is in vacation mode.')
    elif atwar:
        status = warnotok('You\'re already at war with this world.')
    elif target in world.declaredwars.all():
        status = warnotok('You\'ve recently declared war on this world.')
    elif world.warsperturn == 3:
        status = warnotok('You\'ve declared too many wars this turn.')
    elif v.now() < (target.creationtime + time.timedelta(weeks=1)) and target.noobprotect:
        status = warnotok('You cannot declare war on such a new world.')
    elif v.now() < target.warprotection:
        status = warnotok('This world is in war protection.')
    elif (target.gdp < 0.75*(world.gdp)) and (v.now() > target.abovegdpprotection):
        status = warnotok('This world is too small to declare war on.')
    elif target.wardefender.count() == 3:
        status = warnotok('This world already has the max quota of defensive wars.')
    elif world.warattacker.count() == 3:
        status = warnotok('You already have the max quota of offensive wars.')
    elif powerok:
        status = warnotok('You do not have enough fleet power to declare war on this world.')
    else:
        title = ''
        if v.now() < world.warprotection:
            title += 'You are currently in war protection. '

        if target.gdp > 3 * world.gdp:
            title += 'This world is above your GDP cap.'

        if title != '':
            status = warwarning(title)
        else:
            status = warok('You can declare war on this world.')

    return mark_safe(status)


register.simple_tag(warstatus)
