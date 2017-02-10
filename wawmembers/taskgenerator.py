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
    if amount > 1:
        return '%s %s are being built and will be delivered in:' % (amount, shiptype)
    else:
        return '%s %s is being built and will be delivered in:' % (amount, shiptype)


def buildpersonalship(shiptype):
    name = display.personalshipname(shiptype)
    return 'Your %s will be ready in' % name


def warpfleet(fleetname, regionfrom, regionto):

    toreturn = 'Your fleet %s will warp from %s to %s in' \
        % (fleetname, regionfrom, regionto)

    return toreturn

def recallfleet(fleetname, worldname, sector):
    return "Your fleet %s has been recalled from %s and will arrive in %s in" % (
        fleetname, worldname, sector)

def sendbackfleet(fleetname, worldname, sector):
    return "%s has sent back fleet %s. It will arrive in %s in" % (
        worldname, fleetname, sector)


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


def directaidarrival(world, resources):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    resource_text = utilities.resource_text(resources)
    return 'We are being sent %s by %s! The shipment will arrive in' \
        % (resource_text, fullworld)

def shipaidarrival(world, ship, amount):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return 'We are being sent %s %s by %s! The shipment will arrive in' \
        % (amount, ship, fullworld)


def tradeaccepterarrival(world, resname, amount):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return 'The %(amount)s %(name)s from our trade with %(world)s will arrive in' \
        % {'amount':amount, 'name':resname, 'world':fullworld}


def tradeownerarrival(world, resname, amount):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return '%(world)s has accepted our trade! The %(amount)s %(name)s will arrive in' \
        % {'amount':amount, 'name':resname, 'world':fullworld}
