# Django Imports
from django.core.urlresolvers import reverse

# Python Imports
import decimal, random

# WaW Imports
from wawmembers.models import World, NewsItem, Agreement, AgreementLog

'''
Misc utility functions for turnchange.
'''

D = decimal.Decimal

################
### CALCULATIONS
################

def toadd(world):
    if world.region == 'A':
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
        grostab = -5
    elif -80 <= world.stability < -60:
        grostab = -2
    elif -60 <= world.stability < -40:
        grostab = -1
    elif 40 <= world.stability < 60:
        grostab = 1
    elif 60 <= world.stability < 80:
        grostab = 2
    elif world.stability >= 80:
        grostab = 5
    return grostab


def tradeavailability(world):
    from wawmembers.utilities import freighterregion
    count = freighterregion(world, world.region)
    agreementlist = list(Agreement.objects.filter(sender=world).exclude(order=0).order_by('order')) + \
        list(Agreement.objects.filter(sender=world, order=0))
    for agreement in agreementlist:
        if agreement.sender != agreement.receiver:
            count -= 1
            if count <= 0:
                agreement.available = False
                agreement.save(update_fields=['available'])
                AgreementLog.objects.create(owner=agreement.sender, target=agreement.receiver, resource=agreement.resource, logtype=4)
                AgreementLog.objects.create(owner=agreement.receiver, target=agreement.sender, resource=agreement.resource, logtype=5)


def grotrade(world, availableonly=False):
    lol = []
    growth = geu = 0

    for restype in xrange(1, 13):
        if availableonly:
            lol.append(list(Agreement.objects.filter(receiver=world, resource=restype, available=True)))
        else:
            lol.append(list(Agreement.objects.filter(receiver=world, resource=restype)))

    for index, res in enumerate(lol):
        lol[index] = [1 for agreement in res]
        lol[index].extend([0] * (12 - len(res)))

    from wawmembers.utilities import lolindexoutcome
    for index in xrange(0,10):
        toaddgrowth, toaddgeu = lolindexoutcome(world, lol, index)
        growth += toaddgrowth
        geu += toaddgeu

    return growth, geu


def groind(world, allocated):
    if world.econsystem == 1:
        growth = rem = 0
    elif world.econsystem == 0:
        growth, rem = divmod(allocated, D(80))
    elif world.econsystem == -1:
        growth, rem = divmod(allocated, D(60))
    return growth, rem


def groindvar(groind):
    if 0 < groind <= 10:
        var = random.randint(-1,1)
    elif 10 < groind <= 20:
        var = random.randint(-2, 2)
    elif 20 < groind <= 30:
        var = random.randint(-3, 3)
    elif 30 < groind <= 40:
        var = random.randint(-4, 4)
    else:
        var = 0
    return var


def fuelcost(world):
    import wawmembers.utilities as utilities
    cost = 0.25 * utilities.warpfuelcost([
        (world.fighters_inA + world.fighters_inB + world.fighters_inC + world.fighters_inD + world.fighters_inS),
        (world.corvette_inA + world.corvette_inB + world.corvette_inC + world.corvette_inD + world.corvette_inS),
        (world.light_cruiser_inA + world.light_cruiser_inB + world.light_cruiser_inC + world.light_cruiser_inD + world.light_cruiser_inS),
        (world.destroyer_inA + world.destroyer_inB + world.destroyer_inC + world.destroyer_inD + world.destroyer_inS),
        (world.frigate_inA + world.frigate_inB + world.frigate_inC + world.frigate_inD + world.frigate_inS),
        (world.heavy_cruiser_inA + world.heavy_cruiser_inB + world.heavy_cruiser_inC + world.heavy_cruiser_inD + world.heavy_cruiser_inS),
        (world.battlecruiser_inA + world.battlecruiser_inB + world.battlecruiser_inC + world.battlecruiser_inD + world.battlecruiser_inS),
        (world.battleship_inA + world.battleship_inB + world.battleship_inC + world.battleship_inD + world.battleship_inS),
        (world.dreadnought_inA + world.dreadnought_inB + world.dreadnought_inC + world.dreadnought_inD + world.dreadnought_inS)]
        )
    return int(cost)


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
def growthnotif(grotrade, grostab, gropol, groind):
    total = grotrade + grostab + gropol + groind
    data = 'Your gdp increased by %s over the turnchange.' % total
    details = ''
    if grotrade > 0:
        details += '<span style=\"color:green;\">%s</span> from trading, ' % grotrade
    if grostab > 0:
        details += '<span style=\"color:green;\">%s</span> from stability, ' % grostab
    elif grostab < 0:
        details += '<span style=\"color:red;\">%s</span> from stability, ' % grostab
    if gropol > 0:
        details += '<span style=\"color:green;\">%s</span> from policies, ' % gropol
    if groind > 0:
        details += '<span style=\"color:green;\">%s</span> from industrial program, ' % groind
    if details != '':
        data += ' (%s)' % details[:-2]
    return data


def groallocnotif(under):
    data = ('You did not have enough money to fully fund your industrial program!' if under else '')
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

    linkdefender = reverse('stats_ind', args=(defender.worldid,))
    fulldefender = '<a href="%(link)s">%(defender)s</a>' % {'link':linkdefender,'defender':defender.world_name}
    NewsItem.objects.create(target=attacker, content=data % fulldefender)

    linkattacker = reverse('stats_ind', args=(attacker.worldid,))
    fullattacker = '<a href="%(link)s">%(attacker)s</a>' % {'link':linkattacker,'attacker':attacker.world_name}
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

    admin = World.objects.get(worldid=1)
    stuff = '<p>&nbsp;&nbsp;'.join(commlist)
    data = "<b>%(type)s Multies:</b> <p>&nbsp;&nbsp;%(stuff)s" % {'type':multitype,'stuff':stuff}
    NewsItem.objects.create(target=admin, content=data)


# No fuel
def nofuel(world):
    data = "You ran out of fuel last turn! Your fleet suffers heavy weariness losses."
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
    world.fighters_inA = int(world.fighters_inA/2)
    world.corvette_inA = int(world.corvette_inA/2)
    world.light_cruiser_inA = int(world.light_cruiser_inA/2)
    world.destroyer_inA = int(world.destroyer_inA/2)
    world.frigate_inA = int(world.frigate_inA/2)
    world.heavy_cruiser_inA = int(world.heavy_cruiser_inA/2)
    world.battlecruiser_inA = int(world.battlecruiser_inA/2)
    world.battleship_inA = int(world.battleship_inA/2)
    world.dreadnought_inA = int(world.dreadnought_inA/2)
    world.fighters_inB = int(world.fighters_inB/2)
    world.corvette_inB = int(world.corvette_inB/2)
    world.light_cruiser_inB = int(world.light_cruiser_inB/2)
    world.destroyer_inB = int(world.destroyer_inB/2)
    world.frigate_inB = int(world.frigate_inB/2)
    world.heavy_cruiser_inB = int(world.heavy_cruiser_inB/2)
    world.battlecruiser_inB = int(world.battlecruiser_inB/2)
    world.battleship_inB = int(world.battleship_inB/2)
    world.dreadnought_inB = int(world.dreadnought_inB/2)
    world.fighters_inC = int(world.fighters_inC/2)
    world.corvette_inC = int(world.corvette_inC/2)
    world.light_cruiser_inC = int(world.light_cruiser_inC/2)
    world.destroyer_inC = int(world.destroyer_inC/2)
    world.frigate_inC = int(world.frigate_inC/2)
    world.heavy_cruiser_inC = int(world.heavy_cruiser_inC/2)
    world.battlecruiser_inC = int(world.battlecruiser_inC/2)
    world.battleship_inC = int(world.battleship_inC/2)
    world.dreadnought_inC = int(world.dreadnought_inC/2)
    world.fighters_inD = int(world.fighters_inD/2)
    world.corvette_inD = int(world.corvette_inD/2)
    world.light_cruiser_inD = int(world.light_cruiser_inD/2)
    world.destroyer_inD = int(world.destroyer_inD/2)
    world.frigate_inD = int(world.frigate_inD/2)
    world.heavy_cruiser_inD = int(world.heavy_cruiser_inD/2)
    world.battlecruiser_inD = int(world.battlecruiser_inD/2)
    world.battleship_inD = int(world.battleship_inD/2)
    world.dreadnought_inD = int(world.dreadnought_inD/2)
    world.fighters_inS = int(world.fighters_inS/2)
    world.corvette_inS = int(world.corvette_inS/2)
    world.light_cruiser_inS = int(world.light_cruiser_inS/2)
    world.destroyer_inS = int(world.destroyer_inS/2)
    world.frigate_inS = int(world.frigate_inS/2)
    world.heavy_cruiser_inS = int(world.heavy_cruiser_inS/2)
    world.battlecruiser_inS = int(world.battlecruiser_inS/2)
    world.battleship_inS = int(world.battleship_inS/2)
    world.dreadnought_inS = int(world.dreadnought_inS/2)
    world.fighters_inH = int(world.fighters_inH/2)
    world.corvette_inH = int(world.corvette_inH/2)
    world.light_cruiser_inH = int(world.light_cruiser_inH/2)
    world.destroyer_inH = int(world.destroyer_inH/2)
    world.frigate_inH = int(world.frigate_inH/2)
    world.heavy_cruiser_inH = int(world.heavy_cruiser_inH/2)
    world.battlecruiser_inH = int(world.battlecruiser_inH/2)
    world.battleship_inH = int(world.battleship_inH/2)
    world.dreadnought_inH = int(world.dreadnought_inH/2)
    world.save()

    data = "The people have finally risen up and deposed their hated ruler! Half your fleet has defected, \
            but you now have a clean slate to rebuild your government."
    NewsItem.objects.create(target=world, content=data)
