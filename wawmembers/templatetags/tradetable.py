# Django Imports
from django import template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

# WaW Imports
from wawmembers.models import World, Agreement
from wawmembers.templatetags.filters import notostring
import wawmembers.utilities as utilities

'''
HTML for trade table display.
'''

register = template.Library()


def tradetable(index, agreelist, listindex):

    try:
        agreement = agreelist[index]
    except IndexError:
        return '-'
    else:
        if agreement.sender == agreement.receiver:
            toreturn = '<span style="color:green;">Surplus</span>'
        else:
            if Agreement.objects.filter(sender=agreement.receiver, receiver=agreement.sender).exists():
                toreturn = '<span style="color:green;font-size:16pt;">+</span> <span class="tip" id="%(id)s">From: <a href="%(link)s">%(name)s</a></span>'
            else:
                toreturn = '<span style="color:yellow;font-size:16pt;">+</span> \
                    <span class="tip" id="%(id)s">From: <a href="%(link)s">%(name)s</a><br>You are not reciprocating this trade.</span>'

        return mark_safe(toreturn % {'id':notostring(index)+notostring(listindex),
            'link':reverse('stats_ind', args=(agreement.sender.worldid,)), 'name':agreement.sender.world_name})

register.simple_tag(tradetable)


def tradetablestatus(worldid, lol, lolindex):

    if lolindex >= 10:
        return '-'

    world = World.objects.get(worldid=worldid)
    newlol = list(lol)

    for index, res in enumerate(newlol):
        newlol[index] = [1 for agreement in res]
        newlol[index].extend([0] * (12 - len(res)))

    growth, geu = utilities.lolindexoutcome(world, newlol, lolindex)

    if growth > 0 and geu > 0:
        toreturn = '%s growth <br> %s GEU' % (growth, geu)
    elif growth > 0:
        toreturn = '%s growth' % growth
    elif geu > 0:
        toreturn = '%s GEU' % geu
    else:
        toreturn = '-'

    return mark_safe(toreturn)

register.simple_tag(tradetablestatus)


def outgoingstatus(worldid, agreement):

    world = World.objects.get(worldid=worldid)

    if agreement.receiver != world:
        if Agreement.objects.filter(sender=agreement.receiver, receiver=world):
            toreturn = '<a href="%s" style="color:green;">%s</a>' \
                % (reverse('stats_ind', args=(agreement.receiver.worldid,)), agreement.receiver)
        else:
            toreturn = '<a href="%s" style="color:yellow;">%s</a>' \
                % (reverse('stats_ind', args=(agreement.receiver.worldid,)), agreement.receiver)
    else:
        toreturn = agreement.receiver

    return mark_safe(toreturn)

register.simple_tag(outgoingstatus)
