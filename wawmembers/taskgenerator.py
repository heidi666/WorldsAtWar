# Django Imports
from django.core.urlresolvers import reverse

# WaW Imports
import wawmembers.display as display
import wawmembers.utilities as utilities
from wawmembers.utilities import plural as pl

'''
Text generation for tasks.
'''


def buildfreighter(amount):
    pluralise = ('%s ' % amount if amount > 1 else '')
    return 'Your %s%s will be ready in' % (pluralise, pl('freighter', amount))


def buildship(shiptype, amount):
    name = utilities.resname(shiptype+10, amount, lower=True)
    return 'Your %s %s will be ready in' % (amount, name)


def buildpersonalship(shiptype):
    name = display.personalshipname(shiptype)
    return 'Your %s will be ready in' % name


def moveship(shiptype, amount, regionfrom, regionto):

    shipname = utilities.resname(shiptype+10, amount, lower=True)

    fromname = display.region_display(regionfrom)
    toname = display.region_display(regionto)

    toreturn = 'Your %(amount)s %(ship)s will warp from %(from)s to %(to)s in' \
        % {'amount':amount, 'ship':shipname, 'from':fromname, 'to':toname}

    return toreturn, shipname


def movepersonalship(regionfrom, regionto):

    fromname = display.region_display(regionfrom)
    toname = display.region_display(regionto)

    toreturn = 'Your personal ship will warp from %(from)s to %(to)s in' \
        % {'from':fromname, 'to':toname}

    return toreturn


def movefreighter(amount, regionfrom, regionto):

    fromname = display.region_display(regionfrom)
    toname = display.region_display(regionto)

    return 'Your %(amount)s %(pl)s will warp from %(from)s to %(to)s in' \
        % {'amount':amount, 'pl':pl('freighter', amount), 'from':fromname, 'to':toname}


def mothball(shiptype, amount, direction):

    shipname = utilities.resname(shiptype+10, amount, lower=True)
    pluralise = ('is' if amount == 1 else 'are')

    if direction == 'plus':
        message = 'Your %s %s %s decommissioning, and will enter the orbital hangars in' % (amount, shipname, pluralise)
    elif direction == 'minus':
        message = 'Your %s %s %s preparing to resume service, and will be ready in' % (amount, shipname, pluralise)

    return message, shipname


def directaidarrival(world, resname, amount):
    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':world.world_name}

    return 'We are being sent %(amount)s %(name)s by %(world)s! The shipment will arrive in' \
        % {'amount':amount, 'name':resname, 'world':fullworld}


def tradeaccepterarrival(world, resname, amount):
    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':world.world_name}

    return 'The %(amount)s %(name)s from our trade with %(world)s will arrive in' \
        % {'amount':amount, 'name':resname, 'world':fullworld}


def tradeownerarrival(world, resname, amount):
    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':world.world_name}

    return '%(world)s has accepted our trade! The %(amount)s %(name)s will arrive in' \
        % {'amount':amount, 'name':resname, 'world':fullworld}
