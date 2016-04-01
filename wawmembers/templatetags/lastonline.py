# Django Imports
from django import template
from django.utils.safestring import mark_safe

# WaW Imports
from wawmembers.models import World
import wawmembers.variables as v

'''
Implements the last online feature.
'''

register = template.Library()

def longtimeformat(delta):
    days = delta.days
    timedeltaseconds = delta.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days == 1:
        return '<p>Last seen: %(days)s day, %(hours)s hr ago</p>' % {'days':days,'hours':hours}
    elif days > 1:
        return '<p>Last seen: %s days ago</p>' % days
    elif hours == 0 and minutes < 10:
        return '<p style="color:green;">Online</p>'
    elif hours == 0:
        return '<p>Last seen: %s minutes ago</p>' % minutes
    else:
        return '<p>Last seen: %(hours)s hr %(minutes)s min ago</p>' % {'hours':hours,'minutes':minutes}


def lastonline(worldid):

    try:
        world = World.objects.get(worldid=worldid)
    except:
        return ''

    lastonline = world.lastloggedintime
    delta = v.now() - lastonline
    toreturn = longtimeformat(delta)

    return mark_safe(toreturn)


register.simple_tag(lastonline)
