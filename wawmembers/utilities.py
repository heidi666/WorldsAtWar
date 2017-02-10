# Django Imports
from django.db.models import F
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import decimal, random, math, datetime

# WaW Imports
from wawmembers.models import *
import wawmembers.display as display
import wawmembers.variables as v
import wawmembers.turnupdates as update
import wawmembers.outcomes_policies as outcomes

'''
Misc functions that are used by other files.
'''

D = decimal.Decimal

###########
### GENERAL
###########

def plural(word, amount):
    'Pluralises words.'
    if amount == 1:
        return word
    else:
        return word + 's'

#this shit heidi
#what the fuck
def levellist():
    'Returns a list of millevels.'
    return v.millevel('cor'), v.millevel('lcr'), v.millevel('des'), v.millevel('fri'), \
     v.millevel('hcr'), v.millevel('bcr'), v.millevel('bsh'), v.millevel('dre')


def timedeltadivide(timediff):
    'Splits a timedelta into h:m:s.'
    timedeltaseconds = timediff.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    minutes = str(minutes).zfill(2)
    seconds = str(seconds).zfill(2)
    return hours, minutes, seconds


def mildisplaylist(world, main=True):
    'Formats data for display on a world page.'
    # displays ships in regions, home region first
    fleets = world.controlled_fleets.all().exclude(sector="warping")
    milinfo = {
    'amyntas': {'max': 0, 'current': 0, 'training': 0, 'power': 0, 'training-level': 0, 
        'totalships': fleet(world=world), 'fuelcost': 0, 'weariness': 0, 'fleets': 0},
    'bion': {'max': 0, 'current': 0, 'training': 0, 'power': 0, 'training-level': 0, 
        'totalships': fleet(world=world), 'fuelcost': 0, 'weariness': 0, 'fleets': 0},
    'cleon': {'max': 0, 'current': 0, 'training': 0, 'power': 0, 'training-level': 0, 
        'totalships': fleet(world=world), 'fuelcost': 0, 'weariness': 0, 'fleets': 0},
    'draco': {'max': 0, 'current': 0, 'training': 0, 'power': 0, 'training-level': 0, 
        'totalships': fleet(world=world), 'fuelcost': 0, 'weariness': 0, 'fleets': 0},
    }
    if main:
        milinfo.update({'hangar': {'max': 0, 'current': 0, 'training': 0, 'power': 0, 'training-level': 0, 
        'totalships': fleet(world=world), 'fuelcost': 0, 'weariness': 0, 'fleets': 0}})
    else:
        fleets = fleets.exclude(sector="hangar")
    for f in fleets:
        milinfo[f.sector]['fuelcost'] += f.fuelcost()
        milinfo[f.sector]['max'] += f.maxtraining()
        milinfo[f.sector]['current'] += f.training
        if f.enoughfuel():
            milinfo[f.sector]['power'] += f.power()
        else:
            milinfo[f.sector]['power'] += f.powerfuel()
        milinfo[f.sector]['totalships'].merge(f)
        milinfo[f.sector]['weariness'] += f.weariness
        milinfo[f.sector]['fleets'] += 1
    #set training level per sector
    for field in milinfo:
        milinfo[field]['training-level'] = display.training_display(milinfo[field]['current'], milinfo[field]['max'])
    #now make it easy to display by assembling display order
    displayorder = [world.sector]
    for field in sorted(milinfo):
        if field not in displayorder:
            displayorder.append(field)
    #django loves tuples
    return (milinfo, displayorder)

#legacy
def formshiplist(millevel, shiplist, freighters=False):
    'Splits shiplist for forms according to military level.'

    if millevel < v.millevel('cor'):
        choices = shiplist[:2]
    elif millevel < v.millevel('lcr'):
        choices = shiplist[:3]
    elif millevel < v.millevel('des'):
        choices = shiplist[:4]
    elif millevel < v.millevel('fri'):
        choices = shiplist[:5]
    elif millevel < v.millevel('hcr'):
        choices = shiplist[:6]
    elif millevel < v.millevel('bcr'):
        choices = shiplist[:7]
    elif millevel < v.millevel('bsh'):
        choices = shiplist[:8]
    else:
        choices = shiplist

    if freighters:
        choices.append(('0', 'Freighters'))

    return choices

#setting fleets after exchanging ships
def exchange_set(target, ratio, data, highest): #fleet, other fleets ratio and cleaned form data
    #first off determine the training that needs to be transferred and subtracted
    referenceratio = target.ratio()
    shipsin = fleet() #ships that gets added
    shipsout = fleet()
    change = {}
    for ship in v.shipindices[:v.shipindices.index(highest)+1]:
        key = "%s %s" % (target.pk, ship)
        print target.__dict__[ship] - data[key], ship
        if target.__dict__[ship] - data[key] > 0:
            shipsin.__dict__[ship] = target.__dict__[ship] - data[key]
        elif target.__dict__[ship] - data[key] < 0:
            shipsout.__dict__[ship] = target.__dict__[ship] - data[key]
    shipsout.training = shipsout.maxtraining() * referenceratio
    target.merge(shipsout)
    shipsin.training = shipsin.maxtraining() * ratio
    target.training = (target.maxtraining() * referenceratio) + shipsin.training
    for ship in v.shipindices[:v.shipindices.index(highest)+1]:
        key = "%s %s" % (target.pk, ship)
        target.__dict__[ship] = data[key]



#returns initial data for fleet exchange page
def fleetinit(fleet1, fleet2):
    init = {}
    for ship in v.shipindices:
        init.update({
            '%s %s' % (fleet1.pk, ship): fleet1.__dict__[ship],
            '%s %s' % (fleet2.pk, ship): fleet2.__dict__[ship],
            })
    return init

#######################
### ATOMIC TRANSACTIONS
#######################

#takes a dictionary of actions to take and a primary key to a world and target world
#where said actions are to be taken
#this should avoid race conditions entirely
def atomic_world(pk, actions, targetpk=None):
    with transaction.atomic():
        updatelist = []
        if targetpk is not None:
            world = World.objects.select_for_update().get(pk=pk)
            targetworld = World.objects.select_for_update().get(pk=targetpk)
            #first we do stuff
            for field in actions:
                if actions[field]['action'] is 'subtract':
                    targetworld.__dict__[field] -= actions[field]['amount']
                    world.__dict__[field] += actions[field]['amount']
                else:
                    targetworld.__dict__[field] += actions[field]['amount']
                    world.__dict__[field] -= actions[field]['amount']
                #then we assemble a list of fields to update
                updatelist.append(field)
            targetworld.save(update_fields=updatelist)
        else:
            world = World.objects.select_for_update().get(pk=pk)
            for field in actions:
                if actions[field]['action'] is 'subtract':
                    world.__dict__[field] -= actions[field]['amount']
                elif actions[field]['action'] is 'add':
                    world.__dict__[field] += actions[field]['amount']
                else:
                    world.__dict__[field] = actions[field]['amount']
                #then we assemble a list of fields to update
                updatelist.append(field)
        world.save(update_fields=updatelist)

#takes fleet pk, actions and a pk to target if any
def atomic_fleet(pk, actions, targetpk=None):
    with transaction.atomic():
        playerfleet = fleet.objects.select_for_update().get(pk=pk)
        updatelist = []
        if 'train' in actions:
            playerfleet.train()
            updatelist.append('training')
            #training is 2 part, money subtraction is a seperate function call
        elif 'warp' in actions:
            playerfleet.sector = "warping"
            updatelist.append('sector')

        elif 'add' in actions:
            for field in actions['add']:
                playerfleet.__dict__[field] += actions['add'][field]
                updatelist.append(field)

        elif 'subtractships' in actions:
            ratio = playerfleet.ratio() #to set new 
            for field in actions['subtractships']:
                playerfleet.__dict__[field] -= actions['subtractships'][field]
                updatelist.append(field)
            playerfleet.training = int(ratio * playerfleet.maxtraining())
            playerfleet.attacked = True
            updatelist += ['training', 'attacked']

        elif 'set' in actions:
            for field in actions['set']:
                playerfleet.__dict__[field] = actions['set'][field]
            if 'controller' in actions['set']: #doesn't work with the above for some raisin
                playerfleet.controller = actions['set']['controller']

        elif 'mergeaid' in actions: #merging single ship aid
            mergerfleet = fleet.objects.get(pk=targetpk)
            playerfleet.merge(mergerfleet)
            mergerfleet.delete()
        elif 'merge' in actions:
            mergerfleet = fleet.objects.select_for_update().get(pk=targetpk)
            playerfleet.merge(mergerfleet)
            mergerfleet.save()
        elif 'mergeorder' in actions:
            playerfleet.mergeorder(actions['mergeorder'])
        elif 'loss' in actions:
            playerfleet.loss(actions['loss'])
            playerfleet.attacked = True
            playerfleet.train() #only called after combat and combat ++training;
        elif 'add' in actions:
            for field in actions['add']:
                playerfleet.__dict__[field] += actions['add'][field]

        if updatelist:
            playerfleet.save(update_fields=updatelist)
        else:
            playerfleet.save()


###################
### QUANTITY CHANGE
###################

def attrchange(current, amount, zero=False):
    if current + amount > 100: #return the amount required to reach 100 and -100 respectively
        return amount - (current + amount - 100)
    elif current + amount < -100:
        return amount - (current + amount + 100)
    elif zero and current + amount < 0:
        return amount - (current + amount)
    else:
        return amount

############
### POLICIES
############

#checks if the player can afford to build the ships and returns cost + status
def costcheck(world, order):
    cost = {
        'geu': 0,
        'duranium': 0,
        'tritanium': 0,
        'adamantium': 0,
        'productionpoints': 0,
    }
    status = cost.copy()
    shipcosts = v.shipcosts(world.sector)
    assets = world.buildcapacity()
    goodtogo = True
    #calculate dem costs
    for ship, amount in order.iteritems():
        if amount > 0:
            for key in cost:
                cost[key] += shipcosts[ship][key] * amount
    #compare to current assets
    for key in assets:
        if assets[key] < cost[key]:
            status[key] = False #not enough of a given resource
            goodtogo = False
        else:
            status[key] = True
    status.update({'status': goodtogo, 'cost': cost})
    return status

def rescosts(world):
    'Calculates resource costs.'
    if world.sector == 'cleon':
        warp = 350 + 2*world.warpfuelprod
        dur = 500 + 8*world.duraniumprod
        trit = 900 + 18*world.tritaniumprod
        adam = 1450 + 35*world.adamantiumprod
    else:
        warp = 400 + 2.5*world.warpfuelprod
        dur = 600 + 10*world.duraniumprod
        trit = 1000 + 20*world.tritaniumprod
        adam = 1750 + 40*world.adamantiumprod
    return warp, dur, trit, adam


def martiallawadd(world):
    'Executes martial law by military level.'
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = levellist()
    if world.millevel < corlevel:
        resourcecompletion(world, 11, 10, 0)
    elif corlevel <= world.millevel < lcrlevel:
        resourcecompletion(world, 12, 9, 0)
    elif lcrlevel <= world.millevel < deslevel:
        resourcecompletion(world, 13, 8, 0)
    elif deslevel <= world.millevel < frilevel:
        resourcecompletion(world, 14, 7, 0)
    elif frilevel <= world.millevel < hcrlevel:
        resourcecompletion(world, 15, 6, 0)
    elif hcrlevel <= world.millevel < bcrlevel:
        resourcecompletion(world, 16, 5, 0)
    elif bcrlevel <= world.millevel < bshlevel:
        resourcecompletion(world, 17, 4, 0)
    elif bshlevel <= world.millevel < drelevel:
        resourcecompletion(world, 18, 3, 0)
    elif world.millevel >= drelevel:
        resourcecompletion(world, 19, 2, 0)


def rumsoddiumhandout():
    'Hands out rumsoddium to active worlds.'
    activeworlds = list(World.objects.filter(lastloggedintime__gte=v.now()-datetime.timedelta(days=5)))
    for i in xrange(4):
        luckyworld = random.choice(activeworlds)
        activeworlds.remove(luckyworld)
        luckyworld.rumsoddium = 1
        luckyworld.save(update_fields=['rumsoddium'])
        NewsItem.objects.create(target=luckyworld, content='On a routine patrol, one of your ships encountered a small piece of green \
            substance floating through space. Upon bringing it back for inspection, you scientists confirmed it was a rare piece \
            of rumsoddium! What luck!')


#############
### ALLIANCES
#############

def allsize(alliance):
    'Returns size of alliance.'
    return alliance.allmember.count()


def alliancedata(requestdata, allianceid):
    'Provides various data about an alliance.'
    try:
        alliance = Alliance.objects.get(allianceid=allianceid)
    except ObjectDoesNotExist:
        return None, None, None, None

    members = alliance.allmember.all()
    officers = list(members.filter(officer=True).order_by('pk'))
    try:
        leader = members.get(leader=True)
    except:
        cleanalliance(alliance)
    alliancemembers = list(members.exclude(leader=True).exclude(officer=True))

    if len(alliancemembers) == 0:     # in order to display message if no other members
        alliancemembers = None
    if len(officers) == 0:          # in order to display message if no officers
        officers = None
    return alliance, alliancemembers, officers, leader


def alliancestats(world, alliance, leader, officer, member, displaytype):
    'Decides whether to display alliance stats.'

    officerprefs = alliance.officerstats
    memberprefs = alliance.memberstats
    publicprefs = alliance.publicstats

    if world.alliance == alliance:
        if leader:
            return True
        elif officer:
            if displaytype in officerprefs or displaytype in memberprefs or displaytype in publicprefs:
                return True
            else:
                return False
        else:
            if displaytype in memberprefs or displaytype in publicprefs:
                return True
            else:
                return False
    else:
        if displaytype in publicprefs:
            return True
        else:
            return False


def cleanalliance(alliance):
    'Assigns leader to a vacant alliance. If no members, deletes alliance.'
    members = alliance.allmember.all()
    officers = list(members.filter(officer=True))
    if len(officers) > 0:
        world = officers[0]
        world.officer = False
        world.leader = True
        world.save(update_fields=['officer','leader'])
    elif len(members) > 0:
        world = members[0]
        world.officer = False
        world.leader = True
        world.save(update_fields=['officer','leader'])
    else:
        alliance.delete()


###########
### ECONOMY
###########
#takes a list of lists with shipnames and amounts
#ie [[fighters, 1],[destroyers, 10]]
def resource_text(resources):
    text = ""
    if len(resources) == 1:
            text = "%s %s" % (resources[0][1], resources[0][0])
    else:
        for i, resource in enumerate(resources, 1):
            text += "%s %s" % (resource[1], resource[0])
            if len(resources) - 1 == i:
                text += ' and '
            else:
                text += ', '
        text = text[:-2]
    return text
##########
### TRADES
##########


def tradecost(world, amount):
    'Checks if the trade owner can pay the upfront cost.'
    if world.econsystem == 1:
        cost = 10*amount
    elif world.econsystem == 0:
        cost = 15*amount
    elif world.econsystem == -1:
        cost = 20*amount

    if cost > world.budget:
        return False
    else:
        return True


def militarypower(world, sector):
    fleets = world.controlled_fleets.all().filter(sector=sector)
    power = 0
    for fleet in fleets:
        power += fleet.basepower()
    return power

def shippowerdefwars(world, restype):
    'Calculates/allows power being warped.'
    defwars = list(War.objects.filter(defender=world))
    for war in defwars:
        own = militarypower(world, war.sector)
        attacker = militarypower(war.attacker, war.sector)
        if own < attacker:
            return 'Your generals refuse to warp ships away while under attack from a superior force!'
    return True


def resname(resource, amount=1, lower=False, mapping=False):
    'Returns name from resource number.'
    if resource == 0:
        name = 'GEU'
    if resource == 1:
        name = 'Warpfuel'
    if resource == 2:
        name = 'Duranium'
    if resource == 3:
        name = 'Tritanium'
    if resource == 4:
        name = 'Adamantium'
    if resource == 10:
        name = plural('Freighter', amount)
    if resource == 11:
        name = plural('Fighter', amount)
    if resource == 12:
        name = plural('Corvette', amount)
    if resource == 13:
        name = plural('Light Cruiser', amount)
    if resource == 14:
        name = plural('Destroyer', amount)
    if resource == 15:
        name = plural('Frigate', amount)
    if resource == 16:
        name = plural('Heavy Cruiser', amount)
    if resource == 17:
        name = plural('Battlecruiser', amount)
    if resource == 18:
        name = plural('Battleship', amount)
    if resource == 19:
        name = plural('Dreadnought', amount)

    #map heidis stupid shit to actual variable names for easy manipulation
    if mapping:
        if name == 'GEU':
            return 'budget'
        elif resource < 10:
            return name.lower()
        else:
            if name[-1:] == 's':
                return name.lower()
            else:
                return name.lower() + 's'

    if lower and resource != 0:
        return name.lower()
    else:
        return name


def freightercount(resource, amount):
    'Calculates freighters required for transport of resource.'
    return ((v.freighter_capacity[resource] * amount) / v.freighter_capacity['total']) + 1 



#######
### WAR
#######

def totalpower(world):
    fleets = world.controlled_fleets.all().exclude(sector='hangar')
    power = 0
    for fleet in fleets:
        power += fleet.power()
    return power

def weighted_choice(ships, highest):
    'Returns a weighted choice.'
    totals = []
    running_total = 0
    index = v.fleetindex
    #+1 so we avoid adding freighters to the kill list
    for ship in list(ships._meta.fields)[index+1:index+highest]:
        running_total += ships.__dict__[ship.name]
        totals.append(running_total)

    rnd = random.random() * running_total
    for ship, total in zip(list(ships._meta.fields)[(index+1):(index+highest)], totals):
        if rnd < total:
            if ships.__dict__[ship.name] is 0: #no more negative ships
                return weighted_choice(ships, highest)
            else:
                return ship.name

def highesttier(fleetlist):
    highest = 0
    for ship in v.shipindices:
        if fleetlist.__dict__[ship] > 0:
            highest = ship
    if highest == 0:
        return v.shipindices[0]
    else:
        return highest

def war_losses(damage, shiplist):
    'Distributes battle losses among a fleet.'
    reference = fleet()
    reference.merge(shiplist) #we use a reference here
    #and use an atomic transaction for actual fleet manipulation
    lost = fleet() #to be returned and merged with active fleet
    shipinfo = v.shipcosts()
    highest = v.shipindices.index(highesttier(shiplist))
    highest += 1 #take discrepancy between list indexes and whatever into account
    repeat = 0
    while damage > 0:
        shiplost = weighted_choice(reference, highest)
        if shiplost is None: #fleet got decimated
            return lost
        if damage < shipinfo[shiplost]['damage'] and repeat < 20:
            repeat += 1
        elif repeat >= 20:
            break
        else:
            repeat = 0
            reference.__dict__[shiplost] -= 1
            lost.__dict__[shiplost] += 1
            damage -= shipinfo[shiplost]['damage']
    return lost


def war_result(attpower, defpower, defbasepower, bonus=False):
    'Returns damage of a battle.'
    attack = attpower**1.8
    defense = defpower**1.8
    if bonus:
        defense *= 1.1
    try:
        damageunround = (attack/(attack+defense))*0.7*defbasepower
    except:
        damageunround = 0

    return int(round(damageunround))


def hangargain(world, hangarlist):
    'Adds hangar gains to region.'
    for shiptype, amount in enumerate(hangarlist, start=1):
        if 'receivestaging' in world.shipsortprefs:
            movecomplete(world, shiptype, amount, 'S', 0)
        else:
            movecomplete(world, shiptype, amount, world.sector, 0)


def raidloss(fuelcost, supply):
    'Calculates freighters lost in a raid.'
    minimum = int(supply/4000) + 1
    if fuelcost >= supply:
        initial = minimum
    else:
        minimum = int(supply/4000) + 1
        maximum = int((supply - fuelcost)/200) + 1
        initial = random.randint(minimum, maximum)
    loss = initial + random.randint(0, 5)

    if loss > supply/200 - 5:
        loss = supply/200 - 5

    return loss


def flagshipreset(world):
    'Destroys a world\'s flagship.'
    world.flagshiptype = 0
    world.flagshiplocation = world.sector
    world.flagshipbuild = False
    world.save(update_fields=['flagshiptype','flagshiplocation','flagshipbuild'])


def salvage(loss):
    'Creates salvage from a shiplist.'
    totd = tott = tota = 0
    matcosts = v.shipcosts()
    for ship in list(loss._meta.fields)[v.fleetindex:]:
        totd += matcosts[ship.name]['duranium']*loss.__dict__[ship.name]/random.randint(3, 10)
        tott += matcosts[ship.name]['tritanium']*loss.__dict__[ship.name]/random.randint(3, 10)
        tota += matcosts[ship.name]['adamantium']*loss.__dict__[ship.name]/random.randint(3, 10)
    return int(totd), int(tott), int(tota)


#########
### SPIES
#########

def caught(spy):
    'Calculates if spy is caught.'
    chance = random.randint(1, 100)
    caught = (False if 60 + 0.5*spy.total >= chance else True) # min skill: 60%, max skill: 90%
    caughtmsg = ('<br>Your agent was caught and executed by your target\'s security.' if caught
        else '<br>Despite his failure, our agent was able to evade enemy forces.')

    return caught, caughtmsg


def reveal(spy):
    'Calculates if spy sender is revealed.'
    chance = random.randint(1, 100)
    reveal = (False if 20 + 0.5*spy.total >= chance else True) # min skill: 20%, max skill: 50%
    revmsg = ('<br>Under torture he told his captors all about us.' if reveal
        else '<br>Our spy managed to resist torture and not tell his captors anything about his employers!')

    return reveal, revmsg


def spyintercept(target, sender, resname, resamount):
    'Calculates if received trade or aid is intercepted.'
    from wawmembers.newsgenerator import notifyspyintercept
    spies = Spy.objects.filter(location=target, inteltime__gt=v.now()).exclude(owner=sender)
    for spy in spies:
        chance = random.randint(1, 100)
        if chance <= 2*spy.intelligence:
            htmldata = notifyspyintercept(target, sender, resname, resamount)
            NewsItem.objects.create(target=spy.owner, content=htmldata)


def spyinterceptsend(world, target, resname, resamount):
    'Calculates if sent trade or aid is intercepted.'
    from wawmembers.newsgenerator import notifyspyinterceptsend
    spies = Spy.objects.filter(location=world, inteltime__gt=v.now()).exclude(owner=target)
    for spy in spies:
        chance = random.randint(1, 100)
        if chance <= 2*spy.intelligence:
            htmldata = notifyspyinterceptsend(world, target, resname, resamount)
            NewsItem.objects.create(target=spy.owner, content=htmldata)


############
### TOOLTIPS
############

def powerbreakdown(fleetlist):
    'Power breakdown per fleet.'
    powerlist = ''
    shiplist = fleetlist[2:11]
    if fleetlist[16] < fleetlist[14]:
        powerlist += '<span style="color:red">WARNING: Not enough fuel!<br>Effective fleet power is only %s.</span> \
                      <p class="halfline">&nbsp;</p>' % fleetlist[16]

    powerlist += '<b>Ships</b>:<br>'
    if sum(shiplist) == 0 and not fleetlist[17]:
        powerlist += 'None'
        return powerlist
    elif sum(shiplist) == 0 and fleetlist[17]:
        powerlist += '<b>+50 power</b> from flagship'
        return powerlist

    shiptypes = []
    amounts = []
    if shiplist[0] > 0:
        shiptypes.append('Fig')
        amounts.append(shiplist[0])
    if shiplist[1] > 0:
        shiptypes.append('Cor')
        amounts.append(5*shiplist[1])
    if shiplist[2] > 0:
        shiptypes.append('LCr')
        amounts.append(10*shiplist[2])
    if shiplist[3] > 0:
        shiptypes.append('Des')
        amounts.append(15*shiplist[3])
    if shiplist[4] > 0:
        shiptypes.append('Fri')
        amounts.append(20*shiplist[4])
    if shiplist[5] > 0:
        shiptypes.append('HCr')
        amounts.append(25*shiplist[5])
    if shiplist[6] > 0:
        shiptypes.append('Bcr')
        amounts.append(30*shiplist[6])
    if shiplist[7] > 0:
        shiptypes.append('Bsh')
        amounts.append(35*shiplist[7])
    if shiplist[8] > 0:
        shiptypes.append('Dre')
        amounts.append(40*shiplist[8])

    toaddshiptypes = ''
    for i in shiptypes:
        toaddshiptypes += '<td align="center">%s</td>' % i

    toaddamounts = ''
    for i in amounts:
        toaddamounts += '<td align="center">%s</td>' % i

    table = """<table>
                 <tr><td><b>Shiptype</b></td>%s</tr>
                 <tr><td><b>Power</b></td>%s</tr>
               </table>""" % (toaddshiptypes, toaddamounts)

    powerlist += table

    if fleetlist[17]:
        powerlist += '<p class="halfline">&nbsp;</p><b>+50 power</b> from flagship'

    powerlist += bonustext(shiplist[::-1])

    return powerlist


def bonustext(shiplist):
    'Bonus power breakdown per fleet.'
    bonuspower = '<p class="halfline">&nbsp;</p><b>Bonuses</b>:<br>'
    toadd = ''
    shiptypes = []
    bonustexts = []
    for i in range(len(shiplist)):
        amounts = ''
        x = 1
        for j in range(i+1,len(shiplist)):
            condition = (2**(j-i))*shiplist[i]
            if shiplist[j] >= condition and shiplist[i] > 0 and shiplist[j] > 0:
                if shiptext(i) not in shiptypes:
                    shiptypes.append(shiptext(i))
                amounts += '%s on %s, ' % (condition, shiptext(j))
            elif shiplist[i] > 0 and shiplist[j] > 0:
                if shiptext(i) not in shiptypes:
                    shiptypes.append(shiptext(i))
                amounts += '%s on %s, ' % (shiplist[j], shiptext(j))
            if x % 4 == 0 and len(amounts) > 0:
                amounts += '<br>'
            x += 1
        if amounts:
            toappend = (amounts[:-6] if amounts[-1] == '>' else amounts[:-2])
            bonustexts.append(toappend)

    toadd = ''
    for index in range(len(shiptypes)):
        toadd += '<tr><td align="center">%s</td><td>%s</td></tr>' % (shiptypes[index], bonustexts[index])

    table = """<table>
                 <tr><td align="center"><b>Shiptype</b></td><td align="center"><b>Bonuses</b></td></tr>
                 %s
               </table>""" % toadd

    if not shiptypes:
        return bonuspower + 'None'
    else:
        return bonuspower + table


def shiptext(shiptype):
    'Abbreviation to shortened text.'
    if shiptype == 8:
        return 'Fig'
    elif shiptype == 7:
        return 'Cor'
    elif shiptype == 6:
        return 'LCr'
    elif shiptype == 5:
        return 'Des'
    elif shiptype == 4:
        return 'Fri'
    elif shiptype == 3:
        return 'HCr'
    elif shiptype == 2:
        return 'Bcr'
    elif shiptype == 1:
        return 'Bsh'
    elif shiptype == 0:
        return 'Dre'


def supplydisplay(fleetlist):
    'Fuel breakdown per fleet.'
    fuel = fleetlist[13]
    power = fleetlist[14]
    freighters = fleetlist[15]
    pwf = fleetlist[16]

    difference = fuel - 200*freighters
    amount, remainder = divmod(difference, 200)
    if remainder > 0:
        amount += 1

    if pwf == power:
        toreturn = 'Supplying %(fuel)s fuel.'
    else:
        toreturn = 'Your freighters cannot refuel this fleet! <br> Supplying %(fuel)s fuel. Need %(amount)s more %(pl)s.'

    return toreturn % {'fuel':freighters*200, 'amount':amount, 'pl':plural('freighter', amount)}


def tooltipdisplay(world):
    'Other assorted tooltips.'
    contstab = update.contstab(world)
    contqol = update.contqol(world)
    contreb = update.contreb(world)
    stabcont = update.stabcont(world)
    stabqol = update.stabqol(world)
    stabreb = update.stabreb(world)
    rebstab = update.rebstab(world)
    budgetchange = update.toadd(world).quantize(D('.1'))
    upkeep = update.upkeep(world)
    fuelprod = world.warpfuelprod
    fuelcharge = update.fuelcost(world)
    budgetcap = update.budgetcap(world)
    #grotrade, x = update.grotrade(world)
    grostab = update.grostab(world)
    gropol = world.growth

    if grostab in [-1, -2, -5]:
        gstab = '<span style="color:red;">-%s</span> due to stability<br>' % grostab
    elif grostab in [1, 2, 5]:
        gstab = '<span style="color:green;">+%s</span> due to stability<br>' % grostab
    else:
        gstab = ''

    if contstab > 0:
        cstab = '<span style="color:green;">+</span> due to stability<br>'
    elif contstab < 0:
        cstab = '<span style="color:red;">-</span> due to stability<br>'
    else:
        cstab = ''

    if contqol > 0:
        cqol = '<span style="color:green;">+</span> due to QoL<br>'
    elif contqol < 0:
        cqol = '<span style="color:red;">-</span> due to QoL<br>'
    else:
        cqol = ''

    creb = ('<span style="color:red;">-</span> due to rebels' if contreb < 0 else '')

    if stabcont > 0:
        scont = '<span style="color:green;">+</span> due to perception<br>'
    elif stabcont < 0:
        scont = '<span style="color:red;">-</span> due to perception<br>'
    else:
        scont = ''

    if stabqol > 0:
        sqol = '<span style="color:green;">+</span> due to QoL<br>'
    elif stabqol < 0:
        sqol = '<span style="color:red;">-</span> due to QoL<br>'
    else:
        sqol = ''

    sreb = ('<span style="color:red;">-</span> due to rebels' if stabreb < 0 else '')

    rstab = ('<span style="color:red;">+</span> due to stability' if rebstab > 0 else '')

    if world.warpfuel + world.warpfuelprod - fuelcharge < 0:
        fuelwarning = '<br><span style="color:red;">WARNING</span> - not enough fuel for upkeep!'
    else:
        fuelwarning = ''

    if world.stability >= 80:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:green;">+20%</span> from stability)'
    elif 60 <= world.stability < 80:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:green;">+10%</span> from stability)'
    elif 40 <= world.stability < 60:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:green;">+5%</span> from stability)'
    elif -60 <= world.stability < -40:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:red;">-10%</span> from stability)'
    elif -80 <= world.stability < -60:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:red;">-20%</span> from stability)'
    elif world.stability < -80:
        capmodifier = '&nbsp;&nbsp;Mod: (<span style="color:red;">-40%</span> from stability)'
    else:
        capmodifier = ''

    regionmod = (' (<span style="color:green;">+15%</span> from A)' if world.sector == 'amyntas' else '')

    if world.qol >= 80:
        budgetmodifier = ' (<span style="color:green;">+20%</span> from QoL)'
    elif 60 <= world.qol < 80:
        budgetmodifier = ' (<span style="color:green;">+10%</span> from QoL)'
    elif 40 <= world.qol < 60:
        budgetmodifier = ' (<span style="color:green;">+5%</span> from QoL)'
    elif -40 <= world.qol < -20:
        budgetmodifier = ' (<span style="color:red;">-10%</span> from QoL)'
    elif -60 <= world.qol < -40:
        budgetmodifier = ' (<span style="color:red;">-20%</span> from QoL)'
    elif -80 <= world.qol < -60:
        budgetmodifier = ' (<span style="color:red;">-30%</span> from QoL)'
    elif world.qol < -80:
        budgetmodifier = ' (<span style="color:red;">-40%</span> from QoL)'
    else:
        budgetmodifier = ''
    xs = '<br>Upkeep: <span style="color:red;">-%s</span> every 20 min' % (upkeep)
    listbud = '<div class="tip" id="budget">Income: <span style="color:green;">+%s</span> every 20 min' % (budgetchange) + \
        '<br>&nbsp;&nbsp;Mod: %s%s%s<br>Budget Cap: %s GEU<br>%s</div>' % (regionmod, budgetmodifier, xs, budgetcap, capmodifier)

    listfuel = '''<div class="tip" id="fuel"><span style="color:green;">+%s</span> due to production<br>
                  <span style="color:red;">-%s</span> due to fleet upkeep%s</div>''' % (fuelprod, fuelcharge, fuelwarning)

    #listhomep = '<div class="tip" id="homep">%s</div>' % powerbreakdown(fleets[0])
    #liststagingp = '<div class="tip" id="stagingp">%s</div>' % powerbreakdown(fleets[1])
    #listonep = '<div class="tip" id="onep">%s</div>' % powerbreakdown(fleets[2])
    #listtwop = '<div class="tip" id="twop">%s</div>' % powerbreakdown(fleets[3])
    #listthreep = '<div class="tip" id="threep">%s</div>' % powerbreakdown(fleets[4])
    #listhangarsp = '<div class="tip" id="hangarp">%s</div>' % powerbreakdown(fleets[5])

    #listhomes = '<div class="tip" id="homes">%s</div>' % supplydisplay(fleets[0])
    #liststagings = '<div class="tip" id="stagings">%s</div>' % supplydisplay(fleets[1])
    #listones = '<div class="tip" id="ones">%s</div>' % supplydisplay(fleets[2])
    #listtwos = '<div class="tip" id="twos">%s</div>' % supplydisplay(fleets[3])
    #listthrees = '<div class="tip" id="threes">%s</div>' % supplydisplay(fleets[4])

    if cstab == cqol == creb == '':
        listcont = '<div class="tip" id="cont">No change.</div>'
    else:
        listcont = '<div class="tip" id="cont">%s %s %s</div>' % (cstab,cqol,creb)

    if scont == sqol == sreb == '':
        liststab = '<div class="tip" id="stab">No change.</div>'
    else:
        liststab = '<div class="tip" id="stab">%s %s %s</div>' % (scont,sqol,sreb)

    if rstab == '':
        listreb = '<div class="tip" id="reb">No change.</div>'
    else:
        listreb = '<div class="tip" id="reb">%s</div>' % (rstab)

    if world.growth > 0:
        growthchange = '<span style="color:green;">+%s</span> from growth' % world.growth
    else:
        growthchange = '<span style="color:red;">-%s</span> from growth' % world.growth
    listgdp = '<div class="tip" id="gdp">%s</div>' % growthchange

    contents = "%s%s%s%s%s%s" % (listbud,listgdp,listfuel,listcont,liststab,listreb)

    return contents
