# Django Imports
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import decimal, random, math, datetime

# WaW Imports
from wawmembers.models import World, Alliance, Spy, War, NewsItem, Task, Agreement
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


def mildisplaylist(world):
    'Formats data for display on a world page.'
    # displays ships in regions, home region first
    currentA, maximumA = trainingstatus(world, 'A')
    shiplistA = regionshiplist(world, 'A')
    fuelcostA = warpfuelcost(shiplistA)
    if currentA > maximumA:
        world.fleet_inA_training = maximumA
    if currentA < 0:
        world.fleet_inA_training = 0
    trainingA = display.training_display(currentA, maximumA)
    wearinessA = display.weariness_display(world.fleet_inA_weariness)
    powerA = militarypower(world, 'A')
    pwfA = militarypowerwfuel(world, 'A')
    psinA = flagshipregion(world, 'A')

    currentB, maximumB = trainingstatus(world, 'B')
    shiplistB = regionshiplist(world, 'B')
    fuelcostB = warpfuelcost(shiplistB)
    if currentB > maximumB:
        world.fleet_inB_training = maximumB
    if currentB < 0:
        world.fleet_inB_training = 0
    trainingB = display.training_display(currentB, maximumB)
    wearinessB = display.weariness_display(world.fleet_inB_weariness)
    powerB = militarypower(world, 'B')
    pwfB = militarypowerwfuel(world, 'B')
    psinB = flagshipregion(world, 'B')

    currentC, maximumC = trainingstatus(world, 'C')
    shiplistC = regionshiplist(world, 'C')
    fuelcostC = warpfuelcost(shiplistC)
    if currentC > maximumC:
        world.fleet_inC_training = maximumC
    if currentC < 0:
        world.fleet_inC_training = 0
    trainingC = display.training_display(currentC, maximumC)
    wearinessC = display.weariness_display(world.fleet_inC_weariness)
    powerC = militarypower(world, 'C')
    pwfC = militarypowerwfuel(world, 'C')
    psinC = flagshipregion(world, 'C')

    currentD, maximumD = trainingstatus(world, 'D')
    shiplistD = regionshiplist(world, 'D')
    fuelcostD = warpfuelcost(shiplistD)
    if currentD > maximumD:
        world.fleet_inD_training = maximumD
    if currentD < 0:
        world.fleet_inD_training = 0
    trainingD = display.training_display(currentD, maximumD)
    wearinessD = display.weariness_display(world.fleet_inD_weariness)
    powerD = militarypower(world, 'D')
    pwfD = militarypowerwfuel(world, 'D')
    psinD = flagshipregion(world, 'D')

    currentH, maximumH = trainingstatus(world, 'H')
    shiplistH = regionshiplist(world, 'H')
    if currentH > maximumH:
        world.fleet_inH_training = maximumH
    if currentH < 0:
        world.fleet_inH_training = 0
    trainingH = display.training_display(currentH, maximumH)
    powerH = militarypower(world, 'H')

    currentS, maximumS = trainingstatus(world, 'S')
    shiplistS = regionshiplist(world, 'S')
    fuelcostS = warpfuelcost(shiplistS)
    if currentS > maximumS:
        world.fleet_inS_training = maximumS
    if currentS < 0:
        world.fleet_inS_training = 0
    trainingS = display.training_display(currentS, maximumS)
    powerS = militarypower(world, 'S')
    pwfS = militarypowerwfuel(world, 'S')

    world.save(update_fields=['fleet_inA_training','fleet_inB_training','fleet_inC_training',
        'fleet_inD_training','fleet_inH_training','fleet_inS_training'])

    list1 = ['Amyntas', world.fleetname_inA] + shiplistA + [trainingA, wearinessA, fuelcostA, powerA, world.freighter_inA, pwfA, psinA]
    list2 = ['Bion', world.fleetname_inB] + shiplistB + [trainingB, wearinessB, fuelcostB, powerB, world.freighter_inB, pwfB, psinB]
    list3 = ['Cleon', world.fleetname_inC] + shiplistC + [trainingC, wearinessC, fuelcostC, powerC, world.freighter_inC, pwfC, psinC]
    list4 = ['Draco', world.fleetname_inD] + shiplistD + [trainingD, wearinessD, fuelcostD, powerD, world.freighter_inD, pwfD, psinD]
    list5 = ['Hangars',world.fleetname_inH] + shiplistH + [trainingH, '-', '-', powerH, 0, powerH, False]
    list6 = ['Staging',world.fleetname_inS] + shiplistS + [trainingS, '-', fuelcostS, powerS, world.freighter_inS, pwfS, False]

    if world.region == 'A':
        return list1, list6, list2, list3, list4, list5
    elif world.region == 'B':
        return list2, list6, list1, list3, list4, list5
    elif world.region == 'C':
        return list3, list6, list1, list2, list4, list5
    elif world.region == 'D':
        return list4, list6, list1, list2, list3, list5


def regionshiplist(world, region):
    'Gets list of ships by region.'
    if region == 'A':
        shiplist = [world.fighters_inA, world.corvette_inA, world.light_cruiser_inA, world.destroyer_inA, world.frigate_inA,
                    world.heavy_cruiser_inA, world.battlecruiser_inA, world.battleship_inA, world.dreadnought_inA]
    if region == 'B':
        shiplist = [world.fighters_inB, world.corvette_inB, world.light_cruiser_inB, world.destroyer_inB, world.frigate_inB,
                    world.heavy_cruiser_inB, world.battlecruiser_inB, world.battleship_inB, world.dreadnought_inB]
    if region == 'C':
        shiplist = [world.fighters_inC, world.corvette_inC, world.light_cruiser_inC, world.destroyer_inC, world.frigate_inC,
                    world.heavy_cruiser_inC, world.battlecruiser_inC, world.battleship_inC, world.dreadnought_inC]
    if region == 'D':
        shiplist = [world.fighters_inD, world.corvette_inD, world.light_cruiser_inD, world.destroyer_inD,world.frigate_inD,
                    world.heavy_cruiser_inD, world.battlecruiser_inD, world.battleship_inD, world.dreadnought_inD]
    if region == 'H':
        shiplist = [world.fighters_inH, world.corvette_inH, world.light_cruiser_inH, world.destroyer_inH,world.frigate_inH,
                    world.heavy_cruiser_inH, world.battlecruiser_inH, world.battleship_inH, world.dreadnought_inH]
    if region == 'S':
        shiplist = [world.fighters_inS, world.corvette_inS, world.light_cruiser_inS, world.destroyer_inS,world.frigate_inS,
                    world.heavy_cruiser_inS, world.battlecruiser_inS, world.battleship_inS, world.dreadnought_inS]
    return shiplist


def checkno(amount, allowzero=False):
    'Checks if input is a number.'
    try:
        amount = int(amount)
    except:
        return False
    else:
        if allowzero and amount < 0:
            return False
        elif not allowzero and amount < 1:
            return False
        else:
            return True


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


def flagshipregion(world, region):
    'Checks if a flagship is in the region.'
    if world.flagshiptype != 0 and world.flagshiplocation == region:
        return True
    else:
        return False


###################
### QUANTITY CHANGE
###################

def polsystemchange(world, amount):
    'Adds political system to a world.'
    if world.polsystem + amount > 100:
        world.polsystem = 100
    elif world.polsystem + amount < -100:
        world.polsystem = -100
    else:
        world.polsystem = F('polsystem') + amount
    world.save(update_fields=['polsystem'])


def contentmentchange(world, amount):
    'Adds contentment to a world.'
    if world.contentment + amount > 100:
        world.contentment = 100
    elif world.contentment + amount < -100:
        world.contentment = -100
    else:
        world.contentment = F('contentment') + amount
    world.save(update_fields=['contentment'])


def stabilitychange(world, amount):
    'Adds stability to a world.'
    if world.stability + amount > 100:
        world.stability = 100
    elif world.stability + amount < -100:
        world.stability = -100
    else:
        world.stability = F('stability') + amount
    world.save(update_fields=['stability'])


def qolchange(world, amount):
    'Adds qol to a world.'
    if world.qol + amount > 100:
        world.qol = 100
    elif world.qol + amount < -100:
        world.qol = -100
    else:
        world.qol = F('qol') + amount
    world.save(update_fields=['qol'])


def rebelschange(world, amount):
    'Adds rebel amount to a world.'
    if world.rebels + amount > 100:
        world.rebels = 100
    elif world.rebels + amount < 0:
        world.rebels = 0
    else:
        world.rebels = F('rebels') + amount
    world.save(update_fields=['rebels'])


def trainingchange(world, region, amount):
    'Adds training to a region.'
    if region == 'A':
        if world.fleet_inA_training + amount < 0:
            world.fleet_inA_training = 0
        else:
            world.fleet_inA_training = F('fleet_inA_training') + amount
        world.save(update_fields=['fleet_inA_training'])
    elif region == 'B':
        if world.fleet_inB_training + amount < 0:
            world.fleet_inB_training = 0
        else:
            world.fleet_inB_training = F('fleet_inB_training') + amount
        world.save(update_fields=['fleet_inB_training'])
    elif region == 'C':
        if world.fleet_inC_training + amount < 0:
            world.fleet_inC_training = 0
        else:
            world.fleet_inC_training = F('fleet_inC_training') + amount
        world.save(update_fields=['fleet_inC_training'])
    elif region == 'D':
        if world.fleet_inD_training + amount < 0:
            world.fleet_inD_training = 0
        else:
            world.fleet_inD_training = F('fleet_inD_training') + amount
        world.save(update_fields=['fleet_inD_training'])
    elif region == 'H':
        if world.fleet_inH_training + amount < 0:
            world.fleet_inH_training = 0
        else:
            world.fleet_inH_training = F('fleet_inH_training') + amount
        world.save(update_fields=['fleet_inH_training'])
    elif region == 'S':
        if world.fleet_inS_training + amount < 0:
            world.fleet_inS_training = 0
        else:
            world.fleet_inS_training = F('fleet_inS_training') + amount
        world.save(update_fields=['fleet_inS_training'])


def wearinesschange(world, region, amount):
    'Adds weariness to region.'
    if region == 'A':
        if world.fleet_inA_weariness + amount > 200:
            world.fleet_inA_weariness = 200
        elif world.fleet_inA_weariness + amount < 0:
            world.fleet_inA_weariness = 0
        else:
            world.fleet_inA_weariness = F('fleet_inA_weariness') + amount
        world.save(update_fields=['fleet_inA_weariness'])
    if region == 'B':
        if world.fleet_inB_weariness + amount > 200:
            world.fleet_inB_weariness = 200
        elif world.fleet_inB_weariness + amount < 0:
            world.fleet_inB_weariness = 0
        else:
            world.fleet_inB_weariness = F('fleet_inB_weariness') + amount
        world.save(update_fields=['fleet_inB_weariness'])
    if region == 'C':
        if world.fleet_inC_weariness + amount > 200:
            world.fleet_inC_weariness = 200
        elif world.fleet_inC_weariness + amount < 0:
            world.fleet_inC_weariness = 0
        else:
            world.fleet_inC_weariness = F('fleet_inC_weariness') + amount
        world.save(update_fields=['fleet_inC_weariness'])
    if region == 'D':
        if world.fleet_inD_weariness + amount > 200:
            world.fleet_inD_weariness = 200
        elif world.fleet_inD_weariness + amount < 0:
            world.fleet_inD_weariness = 0
        else:
            world.fleet_inD_weariness = F('fleet_inD_weariness') + amount
        world.save(update_fields=['fleet_inD_weariness'])


############
### POLICIES
############

def generalbuild(world, shiptype, amount):
    'Gets variables for shiptype and delegates to build function.'
    cost, dur, trit, adam, yards, hours, x = v.shipcosts(world.region, shiptype)
    result = processship(world, shiptype, amount, cost, dur, trit, adam, yards, hours)
    return result


def processship(world, shiptype, amount, cost, dur, trit, adam, yards, hours):
    'Starts to builds ships.'
    from wawmembers.tasks import buildship
    from wawmembers.taskgenerator import buildship as databuildship
    outcometime = v.now() + datetime.timedelta(hours=hours)
    if not checkno(amount):
        result = "Enter a positive integer."
    else:
        amount = int(amount)
        if world.budget < D(cost*amount):
            result = outcomes.nomoney()
        elif (world.shipyards - world.shipyardsinuse) < yards*amount:
            result = outcomes.notenoughshipyards()
        elif world.duranium < dur*amount:
            result = outcomes.notenoughduranium()
        elif world.tritanium < trit*amount:
            result = outcomes.notenoughtritanium()
        elif world.adamantium < adam*amount:
            result = outcomes.notenoughadamantium()
        else:
            world.budget = F('budget') - D(cost*amount)
            world.duranium = F('duranium') - dur*amount
            world.tritanium = F('tritanium') - trit*amount
            world.adamantium = F('adamantium') - adam*amount
            world.shipyardsinuse = F('shipyardsinuse') + yards*amount
            world.save(update_fields=['budget','duranium','tritanium','adamantium','shipyardsinuse'])
            task = Task(target=world, content=databuildship(shiptype,amount), datetime=outcometime)
            task.save()
            buildship.apply_async(args=(world.worldid, task.pk, shiptype, amount, yards), eta=outcometime)
            result = outcomes.startshipbuild(shiptype,amount)
    return result


def rescosts(world):
    'Calculates resource costs.'
    if world.region == 'C':
        warp = 200 + 4*world.warpfuelprod
        dur = 250 + 45*world.duraniumprod
        trit = 600 + 90*world.tritaniumprod
        adam = 750 + 225*world.adamantiumprod
    else:
        warp = 200 + 5*world.warpfuelprod
        dur = 250 + 50*world.duraniumprod
        trit = 600 + 100*world.tritaniumprod
        adam = 750 + 250*world.adamantiumprod
    res = 10*world.resourceproduction
    return warp, dur, trit, adam, res


def shipdata(region, shiptype):
    'Returns ship data for use on military policies page.'
    cost, dur, trit, adam, shipyards, hours, fuel = v.shipcosts(region, shiptype)

    restext = 'Resources:'
    if dur > 0:
        restext += ' %s duranium' % dur
    if trit > 0:
        restext += ', %s tritanium' % trit
    if adam > 0:
        restext += ', %s adamantium' % adam

    datalist = ['Cost: %s GEU' % cost, restext, 'Shipyards: %s' % shipyards, 'Time: %s hours' % hours, 'Base fuel cost: %s' % fuel]

    return datalist


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


############
### TRAINING
############

def trainingstatus(world, region):
    'Returns current and maximum training for a region.'
    if region == 'A':
        current = world.fleet_inA_training
        maximum = trainingfromlist(regionshiplist(world,'A'))
    elif region == 'B':
        current = world.fleet_inB_training
        maximum = trainingfromlist(regionshiplist(world,'B'))
    elif region == 'C':
        current = world.fleet_inC_training
        maximum = trainingfromlist(regionshiplist(world,'C'))
    elif region == 'D':
        current = world.fleet_inD_training
        maximum = trainingfromlist(regionshiplist(world,'D'))
    elif region == 'H':
        current = world.fleet_inH_training
        maximum = trainingfromlist(regionshiplist(world,'H'))
    elif region == 'S':
        current = world.fleet_inS_training
        maximum = trainingfromlist(regionshiplist(world,'S'))

    return current, maximum


def trainingfromlist(listships):
    'Returns the maximum training of a list of ships.'
    return (listships[0] + 2*listships[1] + 4*listships[2] + 6*listships[3] + 8*listships[4] +
         12*listships[5] + 18*listships[6] + 30*listships[7] + 50*listships[8]) * 10


def trainingcost(world, region):
    'Calculates training cost by region.'
    current, maximum = trainingstatus(world, region)
    try:
        ratio = float(current)/float(maximum)
    except:
        ratio = 0

    cost = (maximum * ratio / 1.5) + 10
    cost = D(cost).quantize(D('.1'))

    return cost


def trainingchangecalc(world, region, shiptype, amount):
    'Calculates trainingchange for warps etc.'
    current, maximum = trainingstatus(world, region)
    listships = [0,0,0,0,0,0,0,0,0]
    listships[shiptype-1] = amount
    trainingloss = trainingfromlist(listships)
    try:
        ratio = float(current)/float(maximum)
    except:
        ratio = 0
    loss = trainingloss*ratio
    return int(round(loss))


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
    officers = list(members.filter(officer=True))
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


#################
### WARPING SHIPS
#################

def movecheck(world, shiptype, amount, regionfrom):
    'Checks if sufficient quantity of a ship is in region.'
    shiplist = regionshiplist(world, regionfrom)
    if shiplist[shiptype-1] < amount:
        return False
    else:
        return True


def movecomplete(world, shiptype, amount, region, trainingch):
    'Adds ships to a region.'
    if region == 'A':
        if shiptype == 1:
            world.fighters_inA = F('fighters_inA') + amount
            world.save(update_fields=['fighters_inA'])
        if shiptype == 2:
            world.corvette_inA = F('corvette_inA') + amount
            world.save(update_fields=['corvette_inA'])
        if shiptype == 3:
            world.light_cruiser_inA = F('light_cruiser_inA') + amount
            world.save(update_fields=['light_cruiser_inA'])
        if shiptype == 4:
            world.destroyer_inA = F('destroyer_inA') + amount
            world.save(update_fields=['destroyer_inA'])
        if shiptype == 5:
            world.frigate_inA = F('frigate_inA') + amount
            world.save(update_fields=['frigate_inA'])
        if shiptype == 6:
            world.heavy_cruiser_inA = F('heavy_cruiser_inA') + amount
            world.save(update_fields=['heavy_cruiser_inA'])
        if shiptype == 7:
            world.battlecruiser_inA = F('battlecruiser_inA') + amount
            world.save(update_fields=['battlecruiser_inA'])
        if shiptype == 8:
            world.battleship_inA = F('battleship_inA') + amount
            world.save(update_fields=['battleship_inA'])
        if shiptype == 9:
            world.dreadnought_inA = F('dreadnought_inA') + amount
            world.save(update_fields=['dreadnought_inA'])

    if region == 'B':
        if shiptype == 1:
            world.fighters_inB = F('fighters_inB') + amount
            world.save(update_fields=['fighters_inB'])
        if shiptype == 2:
            world.corvette_inB = F('corvette_inB') + amount
            world.save(update_fields=['corvette_inB'])
        if shiptype == 3:
            world.light_cruiser_inB = F('light_cruiser_inB') + amount
            world.save(update_fields=['light_cruiser_inB'])
        if shiptype == 4:
            world.destroyer_inB = F('destroyer_inB') + amount
            world.save(update_fields=['destroyer_inB'])
        if shiptype == 5:
            world.frigate_inB = F('frigate_inB') + amount
            world.save(update_fields=['frigate_inB'])
        if shiptype == 6:
            world.heavy_cruiser_inB = F('heavy_cruiser_inB') + amount
            world.save(update_fields=['heavy_cruiser_inB'])
        if shiptype == 7:
            world.battlecruiser_inB = F('battlecruiser_inB') + amount
            world.save(update_fields=['battlecruiser_inB'])
        if shiptype == 8:
            world.battleship_inB = F('battleship_inB') + amount
            world.save(update_fields=['battleship_inB'])
        if shiptype == 9:
            world.dreadnought_inB = F('dreadnought_inB') + amount
            world.save(update_fields=['dreadnought_inB'])

    if region == 'C':
        if shiptype == 1:
            world.fighters_inC = F('fighters_inC') + amount
            world.save(update_fields=['fighters_inC'])
        if shiptype == 2:
            world.corvette_inC = F('corvette_inC') + amount
            world.save(update_fields=['corvette_inC'])
        if shiptype == 3:
            world.light_cruiser_inC = F('light_cruiser_inC') + amount
            world.save(update_fields=['light_cruiser_inC'])
        if shiptype == 4:
            world.destroyer_inC = F('destroyer_inC') + amount
            world.save(update_fields=['destroyer_inC'])
        if shiptype == 5:
            world.frigate_inC = F('frigate_inC') + amount
            world.save(update_fields=['frigate_inC'])
        if shiptype == 6:
            world.heavy_cruiser_inC = F('heavy_cruiser_inC') + amount
            world.save(update_fields=['heavy_cruiser_inC'])
        if shiptype == 7:
            world.battlecruiser_inC = F('battlecruiser_inC') + amount
            world.save(update_fields=['battlecruiser_inC'])
        if shiptype == 8:
            world.battleship_inC = F('battleship_inC') + amount
            world.save(update_fields=['battleship_inC'])
        if shiptype == 9:
            world.dreadnought_inC = F('dreadnought_inC') + amount
            world.save(update_fields=['dreadnought_inC'])

    if region == 'D':
        if shiptype == 1:
            world.fighters_inD = F('fighters_inD') + amount
            world.save(update_fields=['fighters_inD'])
        if shiptype == 2:
            world.corvette_inD = F('corvette_inD') + amount
            world.save(update_fields=['corvette_inD'])
        if shiptype == 3:
            world.light_cruiser_inD = F('light_cruiser_inD') + amount
            world.save(update_fields=['light_cruiser_inD'])
        if shiptype == 4:
            world.destroyer_inD = F('destroyer_inD') + amount
            world.save(update_fields=['destroyer_inD'])
        if shiptype == 5:
            world.frigate_inD = F('frigate_inD') + amount
            world.save(update_fields=['frigate_inD'])
        if shiptype == 6:
            world.heavy_cruiser_inD = F('heavy_cruiser_inD') + amount
            world.save(update_fields=['heavy_cruiser_inD'])
        if shiptype == 7:
            world.battlecruiser_inD = F('battlecruiser_inD') + amount
            world.save(update_fields=['battlecruiser_inD'])
        if shiptype == 8:
            world.battleship_inD = F('battleship_inD') + amount
            world.save(update_fields=['battleship_inD'])
        if shiptype == 9:
            world.dreadnought_inD = F('dreadnought_inD') + amount
            world.save(update_fields=['dreadnought_inD'])

    if region == 'H':
        if shiptype == 1:
            world.fighters_inH = F('fighters_inH') + amount
            world.save(update_fields=['fighters_inH'])
        if shiptype == 2:
            world.corvette_inH = F('corvette_inH') + amount
            world.save(update_fields=['corvette_inH'])
        if shiptype == 3:
            world.light_cruiser_inH = F('light_cruiser_inH') + amount
            world.save(update_fields=['light_cruiser_inH'])
        if shiptype == 4:
            world.destroyer_inH = F('destroyer_inH') + amount
            world.save(update_fields=['destroyer_inH'])
        if shiptype == 5:
            world.frigate_inH = F('frigate_inH') + amount
            world.save(update_fields=['frigate_inH'])
        if shiptype == 6:
            world.heavy_cruiser_inH = F('heavy_cruiser_inH') + amount
            world.save(update_fields=['heavy_cruiser_inH'])
        if shiptype == 7:
            world.battlecruiser_inH = F('battlecruiser_inH') + amount
            world.save(update_fields=['battlecruiser_inH'])
        if shiptype == 8:
            world.battleship_inH = F('battleship_inH') + amount
            world.save(update_fields=['battleship_inH'])
        if shiptype == 9:
            world.dreadnought_inH = F('dreadnought_inH') + amount
            world.save(update_fields=['dreadnought_inH'])

    if region == 'S':
        if shiptype == 1:
            world.fighters_inS = F('fighters_inS') + amount
            world.save(update_fields=['fighters_inS'])
        if shiptype == 2:
            world.corvette_inS = F('corvette_inS') + amount
            world.save(update_fields=['corvette_inS'])
        if shiptype == 3:
            world.light_cruiser_inS = F('light_cruiser_inS') + amount
            world.save(update_fields=['light_cruiser_inS'])
        if shiptype == 4:
            world.destroyer_inS = F('destroyer_inS') + amount
            world.save(update_fields=['destroyer_inS'])
        if shiptype == 5:
            world.frigate_inS = F('frigate_inS') + amount
            world.save(update_fields=['frigate_inS'])
        if shiptype == 6:
            world.heavy_cruiser_inS = F('heavy_cruiser_inS') + amount
            world.save(update_fields=['heavy_cruiser_inS'])
        if shiptype == 7:
            world.battlecruiser_inS = F('battlecruiser_inS') + amount
            world.save(update_fields=['battlecruiser_inS'])
        if shiptype == 8:
            world.battleship_inS = F('battleship_inS') + amount
            world.save(update_fields=['battleship_inS'])
        if shiptype == 9:
            world.dreadnought_inS = F('dreadnought_inS') + amount
            world.save(update_fields=['dreadnought_inS'])

    trainingchange(world, region, trainingch)


###########
### ECONOMY
###########

def lolindexoutcome(world, lol, lolindex):
    'Calculates growth from trade routes'

    minimum = min([sum(res) for res in lol]) + 2
    filled = sum([res[lolindex] for res in lol])

    if world.econsystem == 1:
        if filled == 12:
            growth = 6
        elif filled >= 10:
            growth = 4
        elif filled >= 5:
            growth = 2
        else:
            growth = 0
        geu = 0

    elif world.econsystem == 0:
        if filled == 12:
            growth = 3
        elif filled >= 10:
            growth = 2
        elif filled >= 5:
            growth = 1
        else:
            growth = 0
        if lolindex < minimum:
            geu = 10*filled
        else:
            geu = 0

    elif world.econsystem == -1:
        growth = 0
        if lolindex < minimum:
            geu = 20*filled
        else:
            geu = 0

    return growth, geu


def getownlist(world):
    'Returns sorted trade routes.'
    return list(Agreement.objects.filter(sender=world).exclude(order=0).order_by('order')) + \
        list(Agreement.objects.filter(sender=world).filter(order=0))


##########
### TRADES
##########

def tradeamount(world, resource, amount):
    'Checks for sufficient resources.'
    if 'sendhome' in world.shipsortprefs:
        shiplist = regionshiplist(world, world.region)
    else:
        shiplist = regionshiplist(world, 'S')
    notenough = 'You do not have enough of that resource!'

    if resource == 0 and world.budget < amount:
        return notenough
    elif resource == 1 and world.warpfuel < amount:
        return notenough
    elif resource == 2 and world.duranium < amount:
        return notenough
    elif resource == 3 and world.tritanium < amount:
        return notenough
    elif resource == 4 and world.adamantium < amount:
        return notenough
    elif 11 <= resource <= 19 and shiplist[resource-11] < amount:
        return notenough
    else:
        return True


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


def tradeshiptech(world, resource):
    'Checks for sufficient ship knowledge.'
    if (resource == 13 and world.millevel < v.millevel('cor')) or \
     (resource == 14 and world.millevel < v.millevel('lcr')) or \
     (resource == 15 and world.millevel < v.millevel('des')) or \
     (resource == 16 and world.millevel < v.millevel('fri')) or \
     (resource == 17 and world.millevel < v.millevel('hcr')) or \
     (resource == 18 and world.millevel < v.millevel('bcr')) or \
     (resource == 19 and world.millevel < v.millevel('bsh')):
        return 'You do not have the knowledge to operate or maintain such ships!'
    else:
        return True


def tradeshippower(world, shiptype, amount):
    'Calculates/allows power being sold.'
    if shiptype < 11:
        return True
    else:
        listships = [0,0,0,0,0,0,0,0,0]
        listships[shiptype-11] = amount
        powerloss = powerfromlist(listships)
        if powerloss + world.powersent > world.startpower * 0.5:
            return 'Your generals refuse to let you sell so much of your domestic fleet!'
        else:
            world.powersent = F('powersent') + powerloss
            world.save(update_fields=['powersent'])
            return True


def shippowerdefwars(world, restype):
    'Calculates/allows power being warped.'
    if restype < 11:
        return True
    else:
        defwars = list(War.objects.filter(defender=world))
        for war in defwars:
            own = militarypower(world, war.region)
            attacker = militarypower(war.attacker, war.region)
            if own < attacker:
                return 'Your generals refuse to warp ships away while under attack from a superior force!'
        return True


def resname(resource, amount=1, lower=False):
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

    if lower and resource != 0:
        return name.lower()
    else:
        return name


def resourcecompletion(world, resource, amount, trainingchange):
    'Adds resource/ships.'
    if resource == 0:
        world.budget = F('budget') + amount
        world.save(update_fields=['budget'])
    elif resource == 1:
        world.warpfuel = F('warpfuel') + amount
        world.save(update_fields=['warpfuel'])
    elif resource == 2:
        world.duranium = F('duranium') + amount
        world.save(update_fields=['duranium'])
    elif resource == 3:
        world.tritanium = F('tritanium') + amount
        world.save(update_fields=['tritanium'])
    elif resource == 4:
        world.adamantium = F('adamantium') + amount
        world.save(update_fields=['adamantium'])
    else:
        if amount < 0 and 'sendstaging' in world.shipsortprefs or amount > 0 and 'receivestaging' in world.shipsortprefs:
            movecomplete(world, resource-10, amount, 'S', trainingchange)
        else:
            movecomplete(world, resource-10, amount, world.region, trainingchange)


def freightercount(resource, amount):
    'Calculates freighters required for transport of resource.'
    if resource == 1:
        amount, remainder = divmod(amount, 200)
    elif resource == 2:
        amount, remainder = divmod(amount, 20)
    elif resource == 3:
        amount, remainder = divmod(amount, 10)
    elif resource == 4:
        amount, remainder = divmod(amount, 2)
    if remainder > 0:
        amount += 1
    return amount


def freighterregion(world, region):
    'Returns no. of freighters in region.'
    if region == 'A':
        return world.freighter_inA
    if region == 'B':
        return world.freighter_inB
    if region == 'C':
        return world.freighter_inC
    if region == 'D':
        return world.freighter_inD
    if region == 'S':
        return world.freighter_inS


def freightercheck(world, region, amount):
    'Checks if sufficient freighters in region.'
    if freighterregion(world, region) >= amount:
        return True
    else:
        return False


def freightertradecheck(world, resource, amount):
    'Checks if freighters for trade.'
    if resource not in [1, 2, 3, 4]:
        return 0, True

    count = freightercount(resource, amount)
    check = freightercheck(world, world.region, count)

    if not check:
        check = 'You do not have enough freighters to transport these goods!'

    return count, check


def freightermove(world, region, amount):
    'Adds freighters to region.'
    if region == 'A':
        world.freighter_inA = F('freighter_inA') + amount
        world.save(update_fields=['freighter_inA'])
    if region == 'B':
        world.freighter_inB = F('freighter_inB') + amount
        world.save(update_fields=['freighter_inB'])
    if region == 'C':
        world.freighter_inC = F('freighter_inC') + amount
        world.save(update_fields=['freighter_inC'])
    if region == 'D':
        world.freighter_inD = F('freighter_inD') + amount
        world.save(update_fields=['freighter_inD'])
    if region == 'S':
        world.freighter_inS = F('freighter_inS') + amount
        world.save(update_fields=['freighter_inS'])


def freighterloss(world, region, amount):
    'Subtracts freighters from region, dividing between home/staging.'
    if region == world.region:
        fhome = freighterregion(world, region)
        fstaging = freighterregion(world, 'S')
        home, staging = stagingdivide(amount, fhome, fstaging, 0.5)
        freightermove(world, region, -home)
        freightermove(world, 'S', -staging)
    else:
        freightermove(world, region, -amount)


#######
### WAR
#######

def noweariness(world, region, quantity):
    if region == "A" and world.fleet_inA_weariness < quantity \
      or region == "B" and world.fleet_inB_weariness < quantity \
      or region == "C" and world.fleet_inC_weariness < quantity \
      or region == "D" and world.fleet_inD_weariness < quantity:
        return True
    else:
        return False


def warpfuelcost(shiplist):
    'Returns fuel cost of a shiplist.'
    cost = shiplist[0] + 2*shiplist[1] + 3*shiplist[2] + 4*shiplist[3] + 5*shiplist[4] + \
            6*shiplist[5] + 8*shiplist[6] + 10*shiplist[7] + 15*shiplist[8]
    return cost


def percenttraining(world, region):
    'Returns percentage training.'
    current, maximum = trainingstatus(world, region)
    try:
        ratio = float(current)/float(maximum)
    except:
        ratio = 0
    modifier = (ratio/10)*5 + 0.5
    return modifier


def percentweariness(world, region):
    'Returns percentage weariness.'
    if region == 'A':
        modifier = (world.fleet_inA_weariness / float(2000))
    if region == 'B':
        modifier = (world.fleet_inB_weariness / float(2000))
    if region == 'C':
        modifier = (world.fleet_inC_weariness / float(2000))
    if region == 'D':
        modifier = (world.fleet_inD_weariness / float(2000))
    if region == 'S':
        modifier = (world.fleet_inA_weariness / float(2000))
    return modifier*5 + 0.5


def addbonus(list):
    'Calculates fleet bonus from a reversed shiplist.'
    bonuspower = 0
    for i in range(len(list)):
        for j in range(i+1,len(list)):
            if list[j] >= (2**(j-i))*list[i]:
                bonuspower += (2**(j-i))*list[i]
            else:
                bonuspower += list[j]
    return bonuspower


def powerfromlist(shiplist, bonus=True):
    'Calculates fleet power from a shiplist.'
    bonuspower = addbonus(shiplist[::-1])
    fig, cor, lcr, des, fri, hcr, bcr, bsh, dre = shiplist

    if bonus:
        return bonuspower + fig + 5*cor + 10*lcr + 15*des + 20*fri + 25*hcr + 30*bcr + 35*bsh + 40*dre
    else:
        return fig + 5*cor + 10*lcr + 15*des + 20*fri + 25*hcr + 30*bcr + 35*bsh + 40*dre


def militarypower(world, region, listships=None, incflagship=True):
    'Returns fleet power from region or shiplist.'

    shiplist = (listships if listships is not None else regionshiplist(world, region))
    power = powerfromlist(shiplist)

    if world is not None:
        if incflagship and flagshipregion(world, region):
            power += 50

    return power


def militarypowerwfuel(world, region, listships=None, incflagship=True):
    'Returns fleet power from region or shiplist, taking fuel into account.'

    fuel = 200*freighterregion(world, region)
    if listships is None:
        listships = regionshiplist(world, region)

    cost = warpfuelcost(listships)
    if incflagship and flagshipregion(world, region):
        cost += 10
    fuellist = [1, 2, 3, 4, 5, 6, 8, 10, 15]

    if fuel >= cost:
        return militarypower(world, region, listships, incflagship)
    else:
        deficit = cost - fuel

    shiplist = [0,0,0,0,0,0,0,0,0]
    skip = False

    for index, shiptype in enumerate(listships):
        if skip:
            shiplist[index] = shiptype
        elif shiptype*fuellist[index] < deficit:
            deficit -= shiptype*fuellist[index]
        else:
            shipno = int(deficit/float(fuellist[index]) + 0.5)
            shiplist[index] = listships[index] - shipno
            skip = True
            deficit = 0

    if deficit > 0:
        return militarypower(world, region, shiplist, False)
    else:
        return militarypower(world, region, shiplist, incflagship)


def weighted_choice(weights):
    'Returns a weighted choice.'
    totals = []
    running_total = 0

    for w in weights:
        running_total += w
        totals.append(running_total)

    rnd = random.random() * running_total
    for i, total in enumerate(totals):
        if rnd < total:
            return i


def war_losses(damage, shiplist):
    'Distributes battle losses among a shiplist.'
    ship0, ship1, ship2, ship3, ship4, ship5, ship6, ship7, ship8 = 0, 0, 0, 0, 0, 0, 0, 0, 0
    while damage > 0:
        shipclasslost = weighted_choice(shiplist)
        if shipclasslost is None:
            return [ship0, ship1, ship2, ship3, ship4, ship5, ship6, ship7, ship8]
        shiplist[shipclasslost] -= 1
        if shipclasslost == 0:
            damage -= 1
            ship0 += 1
        elif shipclasslost == 1:
            damage -= 5
            ship1 += 1
        elif shipclasslost == 2:
            damage -= 10
            ship2 += 1
        elif shipclasslost == 3:
            damage -= 15
            ship3 += 1
        elif shipclasslost == 4:
            damage -= 20
            ship4 += 1
        elif shipclasslost == 5:
            damage -= 25
            ship5 += 1
        elif shipclasslost == 6:
            damage -= 30
            ship6 += 1
        elif shipclasslost == 7:
            damage -= 35
            ship7 += 1
        elif shipclasslost == 8:
            damage -= 40
            ship8 += 1
    return [ship0, ship1, ship2, ship3, ship4, ship5, ship6, ship7, ship8]


def war_result(attpower, defpower, defbasepower, defenselist, bonus=False):
    'Returns damage of a battle.'
    attack = attpower**1.8
    defense = defpower**1.8
    if bonus:
        defense *= 1.1
    try:
        damageunround = (attack/(attack+defense))*0.7*defbasepower
    except:
        damageunround = 0

    damage = int(round(damageunround))

    return war_losses(damage, defenselist)


def warloss_byregion(world, region, losseslist):
    'Battle losses by region.'
    current, maximum = trainingstatus(world, region)
    trainingloss = trainingfromlist(losseslist)
    try:
        ratio = float(current)/float(maximum)
    except:
        ratio = 0
    actualloss = trainingloss*ratio

    for shiptype, amount in enumerate(losseslist, start=1):
        movecomplete(world, shiptype, -amount, region, 0)
    trainingchange(world, region, -actualloss)


def powerallmodifiers(world, region, listships=None, incflagship=True, ignorefuel=False):
    'Returns power (with fuel) including all modifiers.'
    if ignorefuel:
        power = militarypower(world, region, listships, incflagship)
    else:
        power = militarypowerwfuel(world, region, listships, incflagship)

    weamod = (percentweariness(world, world.region) if region == 'S' else percentweariness(world, region))
    trmod = percenttraining(world, region)

    return power*weamod*trmod


def hangargain(world, hangarlist):
    'Adds hangar gains to region.'
    for shiptype, amount in enumerate(hangarlist, start=1):
        if 'receivestaging' in world.shipsortprefs:
            movecomplete(world, shiptype, amount, 'S', 0)
        else:
            movecomplete(world, shiptype, amount, world.region, 0)


def hangarcalculator(world, hangarlist):
    'Returns hangar losses by millevel'
    h1, h2, h3, h4, h5, h6, h7, h8, h9 = hangarlist
    if world.millevel >= v.millevel('dre'):
        return [h1, h2, h3, h4, h5, h6, h7, h8, h9]
    elif world.millevel >= v.millevel('bsh'):
        return [h1, h2, h3, h4, h5, h6, h7, h8, h9]
    elif world.millevel >= v.millevel('bcr'):
        return [h1, h2, h3, h4, h5, h6, h7, h8, 0]
    elif world.millevel >= v.millevel('hcr'):
        return [h1, h2, h3, h4, h5, h6, h7, 0, 0]
    elif world.millevel >= v.millevel('fri'):
        return [h1, h2, h3, h4, h5, h6, 0, 0, 0]
    elif world.millevel >= v.millevel('des'):
        return [h1, h2, h3, h4, h5, 0, 0, 0, 0]
    elif world.millevel >= v.millevel('lcr'):
        return [h1, h2, h3, h4, 0, 0, 0, 0, 0]
    elif world.millevel >= v.millevel('cor'):
        return [h1, h2, h3, 0, 0, 0, 0, 0, 0]
    else:
        return [h1, h2, 0, 0, 0, 0, 0, 0, 0]


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


def stagingdivide(quantity, home, staging, hsratio):
    'Divides losses between home and staging regions.'
    if quantity == 0:
        return 0,0
    lhome = int(math.ceil(quantity*hsratio - 1) + 1)
    lstaging = int(quantity - lhome)
    if lhome <= home and lstaging <= staging:
        return lhome, lstaging
    elif lhome >= home and lstaging >= staging:
        return home, staging
    elif lhome > home:
        diff = lhome - home
        if lstaging+diff >= staging:
            return home, staging
        else:
            return home, lstaging+diff
    elif lstaging > staging:
        diff = lstaging - staging
        if lhome+diff >= home:
            return home, staging
        else:
            return lhome+diff, staging


def staginglosssplit(losslist, homelist, staginglist, hsratio):
    'Applies stagingdivide() to ship lists.'
    home = []
    staging = []
    for i in range(len(losslist)):
        lhome, lstaging = stagingdivide(losslist[i], homelist[i], staginglist[i], hsratio)
        home.append(lhome)
        staging.append(lstaging)
    return home, staging


def flagshipreset(world):
    'Destroys a world\'s flagship.'
    world.flagshiptype = 0
    world.flagshiplocation = world.region
    world.flagshipbuild = False
    world.save(update_fields=['flagshiptype','flagshiplocation','flagshipbuild'])


def salvage(losslist):
    'Creates salvage from a shiplist.'
    totd = tott = tota = 0
    for shiptype, amount in enumerate(losslist, 1):
        dur, trit, adam = v.matcosts(shiptype)
        totd += dur*amount/10.0
        tott += trit*amount/10.0
        tota += adam*amount/10.0
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
    fuelprod = world.warpfuelprod
    fuelcharge = update.fuelcost(world)
    fleets = mildisplaylist(world)
    budgetcap = update.budgetcap(world)
    grotrade, x = update.grotrade(world)
    grostab = update.grostab(world)
    gropol = world.growth
    groind, x = update.groind(world, world.industrialprogram)

    gtrade = ('<span style="color:green;">+%s</span> anticipated from trade<br>' % grotrade if grotrade > 0 else '')

    if grostab in [-1, -2, -5]:
        gstab = '<span style="color:red;">-%s</span> due to stability<br>' % grostab
    elif grostab in [1, 2, 5]:
        gstab = '<span style="color:green;">+%s</span> due to stability<br>' % grostab
    else:
        gstab = ''

    gpol = ('<span style="color:green;">+%s</span> from your policies<br>' % gropol if gropol > 0 else '')

    gind = ('<span style="color:green;">+%s</span> estimated due to industry<br>' % int(groind) if groind > 0 else '')

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

    regionmod = (' (<span style="color:green;">+15%</span> from A)' if world.region == 'A' else '')

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

    listbud = '<div class="tip" id="budget">Income: <span style="color:green;">+%s</span> every 20 min' % (budgetchange) + \
        '<br>&nbsp;&nbsp;Mod: %s%s<br>Budget Cap: %s GEU<br>%s</div>' % (regionmod, budgetmodifier, budgetcap, capmodifier)

    listfuel = '''<div class="tip" id="fuel"><span style="color:green;">+%s</span> due to production<br>
                  <span style="color:red;">-%s</span> due to fleet upkeep%s</div>''' % (fuelprod, fuelcharge, fuelwarning)

    listhomep = '<div class="tip" id="homep">%s</div>' % powerbreakdown(fleets[0])
    liststagingp = '<div class="tip" id="stagingp">%s</div>' % powerbreakdown(fleets[1])
    listonep = '<div class="tip" id="onep">%s</div>' % powerbreakdown(fleets[2])
    listtwop = '<div class="tip" id="twop">%s</div>' % powerbreakdown(fleets[3])
    listthreep = '<div class="tip" id="threep">%s</div>' % powerbreakdown(fleets[4])
    listhangarsp = '<div class="tip" id="hangarp">%s</div>' % powerbreakdown(fleets[5])

    listhomes = '<div class="tip" id="homes">%s</div>' % supplydisplay(fleets[0])
    liststagings = '<div class="tip" id="stagings">%s</div>' % supplydisplay(fleets[1])
    listones = '<div class="tip" id="ones">%s</div>' % supplydisplay(fleets[2])
    listtwos = '<div class="tip" id="twos">%s</div>' % supplydisplay(fleets[3])
    listthrees = '<div class="tip" id="threes">%s</div>' % supplydisplay(fleets[4])

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

    if gstab == gtrade == gpol == gind == '':
        listgdp = '<div class="tip" id="gdp">No change.</div>'
    else:
        listgdp = '<div class="tip" id="gdp">%s %s %s %s</div>' % (gpol, gstab, gtrade, gind)

    contents = "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (listbud,listgdp,listfuel,listcont,liststab,listreb,listhomep,liststagingp,
        listonep,listtwop,listthreep,listhangarsp,listhomes,liststagings,listones,listtwos,listthrees)

    return contents
