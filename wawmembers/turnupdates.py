# Django Imports
from django.core.urlresolvers import reverse

# Python Imports
import decimal, random

# WaW Imports
from wawmembers.models import World, NewsItem
import wawmembers.variables as v
'''
Misc utility functions for turnchange.
'''

D = decimal.Decimal

################
### CALCULATIONS
################

def upkeep(world):
    upkeep = 0
    for entry in v.upkeep:
        upkeep += world.__dict__[entry] * v.upkeep[entry]
    if world.sector == 'cleon':
        upkeep *= 0.8 #total upkeep
    upkeep = D(upkeep) / D(36.0) #3 updates per hour 12 hours per turn
    return upkeep.quantize(D('.1'))

def toadd(world):
    if world.sector == 'amyntas':
        toadd = D((world.gdp/D(36))*D(1.15))
    else:
        toadd = D(world.gdp/D(36))

    if world.qol >= 80:
        modifier = D(1.2)
    elif 60 <= world.qol < 80:
        modifier = D(1.1)
    elif 40 <= world.qol < 60:
        modifier = D(1.05)
    elif -40 <= world.qol < -20:
        modifier = D(0.9)
    elif -60 <= world.qol < -40:
        modifier = D(0.8)
    elif -80 <= world.qol < -60:
        modifier = D(0.7)
    elif world.qol < -80:
        modifier = D(0.6)
    else:
        modifier = D(1)
    return toadd * modifier


def budgetcap(world):
    tempcap = 3*world.gdp

    if world.stability >= 80:
        modifier = 1.15
    elif 60 <= world.stability < 80:
        modifier = 1.1
    elif 40 <= world.stability < 60:
        modifier = 1.05
    elif -60 <= world.stability < -40:
        modifier = 0.9
    elif -80 <= world.stability < -60:
        modifier = 0.8
    elif world.stability < -80:
        modifier = 0.7
    else:
        modifier = 1
    return tempcap * modifier


def contstab(world):
    contstab = 0
    if world.stability < -20:       # -Stability
        contstab = round(world.stability/float(5))
    elif world.stability >= 40:     # +Stability
        contstab = round(world.stability/float(10))
    return contstab


def contqol(world):
    contqol = 0
    if world.qol >= 40:             # +Qol
        contqol = round(world.qol/float(10))
    elif world.qol < -20:           # -Qol
        contqol = round(world.qol/float(2))
    return contqol


def contreb(world):
    contreb = 0
    if world.rebels > 20:           # Rebels
        contreb = round((world.rebels*-1)/float(5))
    return contreb


def stabcont(world):
    stabcont = 0
    if world.polsystem >= 60:           # LibDem
        if world.contentment < -20:     # -Contentment
            stabcont = round(world.contentment/float(4))
        elif world.contentment >= 40:   # +Contentment
            stabcont = round(world.contentment/float(6))
    elif 20 < world.polsystem < 60:     # Tot Dem
        if world.contentment < -20:
            stabcont = round(world.contentment/float(6))
        elif world.contentment >= 40:
            stabcont = round(world.contentment/float(8))
    elif -20 <= world.polsystem <= 20:  # Singleparty
        if world.contentment < -20:
            stabcont = round(world.contentment/float(8))
        elif world.contentment >= 40:
            stabcont = round(world.contentment/float(10))
    elif -60 < world.polsystem < -20:   # Admiralty
        if world.contentment < -20:
            stabcont = round(world.contentment/float(10))
        elif world.contentment >= 40:
            stabcont = round(world.contentment/float(12))
    elif world.polsystem <= -60:        # Autocracy
        if world.contentment < -20:
            stabcont = round(world.contentment/float(12))
        elif world.contentment >= 40:
            stabcont = round(world.contentment/float(14))
    return stabcont


def stabqol(world):
    stabqol = 0
    if world.polsystem >= 60:           # LibDem
        if world.qol >= 40:             # +Qol
            stabqol = round(world.qol/float(18))
        elif world.qol < -20:           # -Qol
            stabqol = round(world.qol/float(6))
    elif 20 < world.polsystem < 60:     # Tot Dem
        if world.qol >= 40:
            stabqol = round(world.qol/float(16))
        elif world.qol < -20:
            stabqol = round(world.qol/float(5))
    elif -20 <= world.polsystem <= 20:  # Singleparty
        if world.qol >= 40:
            stabqol = round(world.qol/float(14))
        elif world.qol < -20:
            stabqol = round(world.qol/float(4))
    elif -60 < world.polsystem < -20:   # Admiralty
        if world.qol >= 40:
            stabqol = round(world.qol/float(12))
        elif world.qol < -20:
            stabqol = round(world.qol/float(3))
    elif world.polsystem <= -60:        # Autocracy
        if world.qol >= 40:
            stabqol = round(world.qol/float(10))
        elif world.qol < -20:
            stabqol = round(world.qol/float(2))
    return stabqol


def stabreb(world):
    stabreb = 0
    if world.rebels > 20:
        stabreb = round((world.rebels*-1)/float(6))
    return stabreb


def rebstab(world):
    rebstab = 0
    if world.stability < -60:
        rebstab = round((abs(world.stability)-50)/float(2))
    return rebstab


def grostab(world):
    grostab = 0
    if world.stability < -80:
        grostab = -4
    elif -80 <= world.stability < -60:
        grostab = -2
    elif -60 <= world.stability < -40:
        grostab = -1
    elif 20 <= world.stability < 40:
        grostab = 1
    elif 40 <= world.stability < 60:
        grostab = 2
    elif 60 <= world.stability < 80:
        grostab = 3
    elif world.stability >= 80:
        grostab = 5
    return grostab


def fuelcost(world):
    import wawmembers.utilities as utilities
    cost = 0
    for blob in world.controlled_fleets.all().exclude(sector='warping').exclude(sector='hangar'):
        cost += blob.fuelcost()
    return int(cost * 0.25)


def growthdecay(world):
    decay = 0
    if world.growth > 45:
        decay = 1
    if world.growth > 60:
        decay = 2
    if world.growth > 70:
        decay = 3
    if world.growth > 75:
        decay = 4
    if world.growth >= 77:
        decay = 5
        decay += 1 + (world.growth-77)*0.2
    return decay


#################
### NOTIFICATIONS
#################

# Tech level change
def techlevelchange(lt, gte, shiptext, shipno):
    updatelist = World.objects.filter(millevel__lt=lt, millevel__gte=gte)
    data = "Through the proliferation of ship technology in the galaxy, your fleet engineers report that they can now " + \
        "successfully produce %s! The prototype has been delivered to the home fleet." % shiptext
    from wawmembers.utilities import movecomplete
    for world in updatelist:
        movecomplete(world, shipno, 1, world.region, 0)
        NewsItem.objects.create(target=world, content=data)

# Contentment
def contstabnotif(contstab):
    if contstab > 0:
        data = "The people's perception of your rule has <span style=\"color:green;\">gone up</span> thanks to your world's high stability!"
    elif contstab < 0:
        data = "Your people's contentment in you has <span style=\"color:red;\">gone down</span> because of your low stability..."
    else:
        data = ''
    return data


def contqolnotif(contqol):
    if contqol > 0:
        data = "Your high standard of life has lead to an <span style=\"color:green;\">increase</span> in the people's happiness!"
    elif contqol < 0:
        data = "The people become <span style=\"color:red;\">more unhappy</span> in you due to their low quality of life!"
    else:
        data = ''
    return data


def contrebnotif(contreb):
    if contreb < 0:
        data = "Your people's confidence in your rule has <span style=\"color:red;\">gone down</span> due to the rebel presence!"
    else:
        data = ''
    return data


# Stability
def stabcontnotif(stabcont):
    if stabcont > 0:
        data = "Your world's stability <span style=\"color:green;\">rises</span> due to the people's high approval of you!"
    elif stabcont < 0:
        data = "Your stability <span style=\"color:red;\">decreases</span> because of the people's dissatisfaction."
    else:
        data = ''
    return data


def stabqolnotif(stabqol):
    if stabqol > 0:
        data = "Your stability has <span style=\"color:green;\">gone up</span> thanks to your high quality of life."
    elif stabqol < 0:
        data = "Your low quality of life leads to <span style=\"color:red;\">a loss</span> of stability in your world!"
    else:
        data = ''
    return data


def stabrebnotif(stabreb):
    if stabreb < 0:
        data = "The presence of rebels in your system <span style=\"color:red;\">lowers</span> your world's stability."
    else:
        data = ''
    return data


# Rebels
def rebstabnotif(rebstab):
    if rebstab < 0:
        data = "Your low stability has led to <span style=\"color:red;\">rebels sprouting up</span> across the system!"
    else:
        data = ''
    return data


# Growth
def growthnotif(grostab, decay):
    total = grostab - decay
    if total < 0:
        data = 'Your gdp decreased by %s over the turnchange.' % (total - total*2)
    else:
        data = 'Your gdp increased by %s over the turnchange.' % total
    details = ''
    if grostab > 0:
        details += '<span style=\"color:green;\">%s</span> from stability, ' % grostab
    elif grostab < 0:
        details += '<span style=\"color:red;\">%s</span> from stability, ' % grostab
    if details != '':
        data += ' (%s)' % details[:-2]
    return data


# Notification
def turndetails(world, updatelist):
    toupdate = []
    for index, value in enumerate(updatelist):
        if value != '':
            toupdate.append(value)

    stuff = ('No special news to report.' if toupdate == [] else '<br>&nbsp;&nbsp;'.join(toupdate))

    data = "<b>Turn Update Notifications:</b> <br>&nbsp;&nbsp;%s" % stuff

    NewsItem.objects.create(target=world, content=data)

# War timeout
def wartimeout(attacker, defender):

    data = "The war between you and %s has timed out, and you are now at peace."

    fulldefender = '<a href="%(link)s">%(defender)s</a>' % {'link':defender.get_absolute_url(),'defender':defender.name}
    NewsItem.objects.create(target=attacker, content=data % fulldefender)

    fullattacker = '<a href="%(link)s">%(attacker)s</a>' % {'link':attacker.get_absolute_url(),'attacker':attacker.name}
    NewsItem.objects.create(target=defender, content=data % fullattacker)


# Trade timeout
def tradetimeout(trade):

    owner = trade.owner

    data = "The trade you posted offering %(amoff)s %(resoff)s for %(amrec)s %(resrec)s has expired, \
            and has been removed from the galactic market." \
            % {'amoff':trade.amountoff,'resoff':trade.displayoff,'amrec':trade.amountrec,'resrec':trade.displayrec}

    NewsItem.objects.create(target=owner, content=data)


# Multi Detection
def multidetect(multilist, multitype):
    #print multilist
    finallist = {}
    commlist = []
    for statcheck, nationlist in multilist.items():
        if len(nationlist) > 1:
            finallist[statcheck] = nationlist
    #print finallist
    if not finallist:
        stuff = 'No multies.'
    else:
        commlist = []
        for statcheck, nationlist in finallist.items():
            for i in range(len(nationlist)):
                linkworld = reverse('stats_ind', args=(nationlist[i],))
                nationlist[i] = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':nationlist[i]}
            nationstring = ', '.join(nationlist)
            commlist.append('%(statcheck)s:  %(list)s' % {'statcheck':statcheck, 'list':nationstring})

    admin = World.objects.get(pk=1)
    stuff = '<p>&nbsp;&nbsp;'.join(commlist)
    data = "<b>%(type)s Multies:</b> <p>&nbsp;&nbsp;%(stuff)s" % {'type':multitype,'stuff':stuff}
    NewsItem.objects.create(target=admin, content=data)


# No fuel
def nofuel(world, fleets):
    fleetnames = ""
    for i, f in enumerate(fleets, 1):
        fleetnames += f.name
        if len(fleets)-1 == i:
            fleetnames += ' and '
        else:
            fleetnames += ', '
    data = "You ran out of fuel last turn! Your fleet%s %s suffers heavy weariness losses." % \
        (('s' if len(fleets) > 1 else ''), fleetnames[:-2])
    NewsItem.objects.create(target=world, content=data)


# Spy in vacation world
def spyvacation(world):
    data = "The world you had infiltrated has been placed in vacation mode. Your spy has been returned."
    NewsItem.objects.create(target=world, content=data)


# GDP RESET
def gdpreset(world):
    world.gdp = 250
    world.growth = 5
    world.budget = 200
    world.warpfuel = int(world.warpfuel/2)
    world.duranium = int(world.duranium/2)
    world.tritanium = int(world.tritanium/2)
    world.adamantium = int(world.adamantium/2)
    world.save()

    data = "A wealthy intergalactic consortium has bailed your world out of its deep economic crisis, but has required \
            heavy payments in the form of your resources."
    NewsItem.objects.create(target=world, content=data)


# STABILITY RESET
def stabreset(world):
    world.gdp = int(world.gdp/2)
    world.growth = (int(world.growth/2) if world.growth > 0 else 0)
    world.budget = int(world.budget/2)
    world.contentment = 0
    world.stability = 0
    world.qol = 0
    world.rebels = 0
    from utilities import atomic_fleet
    for f in world.controlled_fleets.all().filter(world=world):
        actions = {'set': {}}
        for ship in v.shipindices:
            actions['set'].update({ship: f.__dict__[ship] / 2})
        atomic_fleet(f.pk, actions)
    world.save()

    data = "The people have finally risen up and deposed their hated ruler! Half your fleet has defected, \
            but you now have a clean slate to rebuild your government."
    NewsItem.objects.create(target=world, content=data)
