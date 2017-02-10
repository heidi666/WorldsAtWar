# Django Imports
import django
django.setup()
from celery import shared_task, task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.db.models import F
from django.core.urlresolvers import reverse

# Python Imports
import random, datetime
import decimal
import json

# WaW Imports
from wawmembers.models import *
import wawmembers.newsgenerator as news
import wawmembers.display as display
import wawmembers.turnupdates as update
import wawmembers.utilities as utilities
import wawmembers.variables as v

'''
Everything on a timer is here: recurring tasks + tasks after a delay
'''


D = decimal.Decimal

def now():
    return v.now().strftime('%d %b %H:%M:%S')

# every 20 min budget generation
#with upkeep subtracted
@periodic_task(run_every=crontab(minute="0,20,40", hour="*", day_of_week="*"))
def addbudget():
    for world in World.objects.select_related('preferences').all().iterator():
        if world.preferences.vacation:
            continue
        result = 0
        upkeep = 0
        toadd = update.toadd(world).quantize(D('.1')) # round to 1dp
        cap = update.budgetcap(world)
        for entry in v.upkeep:
            upkeep += world.__dict__[entry] * v.upkeep[entry]
        if world.sector == 'cleon':
            upkeep *= 0.8 #total upkeep
        upkeep = D(upkeep) / D(36.0) #3 updates per hour 12 hours per turn
        if world.budget - upkeep > cap:
            continue
        result = toadd - upkeep
        result *= 2
        utilities.atomic_world(world.pk, {'budget': {'action': 'add', 'amount': result}})


# every turn change
@periodic_task(run_every=crontab(minute="1", hour="0, 12", day_of_week="*"))
def worldattributeturnchange():
    GlobalData.objects.filter(pk=1).update(turnbackground=v.background())
    multiloginlist = {}
    for world in World.objects.select_related('preferences').prefetch_related('controlled_fleets').all().iterator():
        if world.preferences.vacation:
            continue
        randomevents(world)
        #heidis multi shit
        try:
            multiloginlist[world.lastloggedinip].append(world.pk)
        except KeyError:
            multiloginlist[world.lastloggedinip] = [world.pk]
        # Value calculationad
        contstab = update.contstab(world)
        contqol = update.contqol(world)
        contreb = update.contreb(world)
        stabcont = update.stabcont(world)
        stabqol = update.stabqol(world)
        stabreb = update.stabreb(world)
        rebstab = update.rebstab(world)
        warpfuel = world.warpfuel + world.warpfuelprod
        change = (world.qol+140)/float(40)
        change = (round(change-1) if change > 0 else round(change-0.5))

        # Text generation
        updatelist = []
        updatelist.append(update.contstabnotif(contstab))
        updatelist.append(update.contqolnotif(contqol))
        updatelist.append(update.contrebnotif(contreb))
        updatelist.append(update.stabcontnotif(stabcont))
        updatelist.append(update.stabqolnotif(stabqol))
        updatelist.append(update.stabrebnotif(stabreb))
        updatelist.append(update.rebstabnotif(rebstab))
        updatelist.append(update.growthnotif(world.growth - update.grostab(world), update.growthdecay(world)))

        # Updates
        fuelcost = fleet_update(world.controlled_fleets.all(), warpfuel)
        rebels = utilities.attrchange(world.rebels, rebstab, zero=True)
        growthincrease = update.grostab(world) - update.growthdecay(world)
        
        actions = {
        'productionpoints': {'action': 'set', 'amount': world.shipyards*12},
        'contentment': {'action': 'add', 'amount': utilities.attrchange(world.contentment, contstab + contreb + contqol)},
        'stability': {'action': 'add', 'amount': utilities.attrchange(world.stability, stabcont + stabqol + stabreb)},
        'rebels': {'action': 'add', 'amount': rebels},
        'qol': {'action': 'subtract', 'amount': change},
        'growth': {'action': 'add', 'amount': growthincrease},
        'turnsalvaged': {'action': 'set', 'amount': False},
        'warpfuel': {'action': 'add', 'amount': world.warpfuelprod - fuelcost},
        'duranium': {'action': 'add', 'amount': world.duraniumprod},
        'tritanium': {'action': 'add', 'amount': world.tritaniumprod},
        'adamantium': {'action': 'add', 'amount': world.adamantiumprod},
        'econchanged': {'action': 'set', 'amount': False},
        'warsperturn': {'action': 'set', 'amount': 0},
        'turnresearched': {'action': 'set', 'amount': False},
        'gdp': {'action': 'add', 'amount': world.growth}
        }
        resetsturnchange(world)
        # Notification
        update.turndetails(world, updatelist)
        utilities.atomic_world(world.pk, actions)
        world.declaredwars.clear()
    #multi stuff
    update.multidetect(multiloginlist, 'Login')
    #chain turn functions instead of time offset
    return shipbuilding_update()

def shipbuilding_update():
    for order in shipqueue.objects.select_related('fleet').all().iterator():
        if order.fleet.world.sector == order.fleet.sector:
            outcome = "%s has been delivered to %s!" % (order.content(), order.fleet.name)
        else:
            outcome = "%s has warped out of the sector! %s was delivered to the hangar" % (
                order.fleet.name, order.content())
            order.fleet = order.world.fleets.all().get(sector="hangar")
        Task.objects.filter(pk=order.task.pk).update(outcome=outcome)
        utilities.atomic_fleet(order.fleet.pk, {'mergeorder': order})
    return spyturnchange()
    
def fleet_update(fleets, available_fuel):
    nofuellist = []
    totalfuelcost = 0
    for f in fleets:
        fuelcost = f.fuelcost() * v.fuelupkeep
        if fuelcost <= available_fuel:
            available_fuel -= f.fuelcost() * v.fuelupkeep
            totalfuelcost += f.fuelcost() * v.fuelupkeep
            fuel = True
        else:
            fuel = False
            nofuellist.append(f)
        fleet_changes(f, fuel)
    if nofuellist:
        update.nofuel(fleets[0].controller, fleets)
    return totalfuelcost

def fleet_changes(tochange, fuel):
    training = tochange.training - (tochange.maxtraining() * (0.1 if tochange.sector == 'hangar' else 0.02))
    if training < 0:
        training = 0
    actions = {'set': {'training': training, 'attacked': False}}
    if fuel:
        weariness = tochange.weariness + 40
        if weariness > 200:
            weariness = 200        
    else:
        weariness = tochange.weariness - 100
        if weariness < 0:
            weariness = 0
    if tochange.sector != 'hangar':
        actions['set'].update({'weariness': weariness})
    utilities.atomic_fleet(tochange.pk, actions)
 
@periodic_task(run_every=crontab(minute="4", hour="0,12", day_of_week="*"))
def techlevels():
    'Tech proliferation.'
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()
    millevels = GlobalData.objects.get(pk=1)
    bcrdis = 100 - int( World.objects.filter(millevel__gte=drelevel).count() / 5.0 )
    hcrdis = 100 - int( World.objects.filter(millevel__lt=drelevel, millevel__gte=bshlevel).count() / 5.0 ) - (100-bcrdis)
    desdis = 100 - int( World.objects.filter(millevel__lt=bshlevel, millevel__gte=bcrlevel).count() / 5.0 ) - (100-hcrdis)
    fridis = 100 - int( World.objects.filter(millevel__lt=bcrlevel, millevel__gte=hcrlevel).count() / 5.0 ) - (100-desdis)
    lcrdis = 100 - int( World.objects.filter(millevel__lt=hcrlevel, millevel__gte=frilevel).count() / 5.0 ) - (100-fridis)
    cordis = 100 - int( World.objects.filter(millevel__lt=frilevel, millevel__gte=deslevel).count() / 5.0 ) - (100-lcrdis)
    bcrdis = (50 if bcrdis < 50 else bcrdis)
    hcrdis = (50 if bcrdis < 50 else hcrdis)
    desdis = (50 if bcrdis < 50 else desdis)
    fridis = (50 if bcrdis < 50 else fridis)
    lcrdis = (50 if bcrdis < 50 else lcrdis)
    cordis = (50 if bcrdis < 50 else cordis)
    if ((v.origbcrlevel/100)*bcrdis) < bcrlevel:
        update.techlevelchange(bcrlevel, (v.origbcrlevel/100)*bcrdis, 'battlecruisers', 7)
        millevels.bcrlevel = (v.origbcrlevel/100)*bcrdis
        millevels.save(update_fields=['bcrlevel'])
    if ((v.orighcrlevel/100)*hcrdis) < hcrlevel:
        update.techlevelchange(hcrlevel, (v.orighcrlevel/100)*hcrdis, 'heavy cruisers', 6)
        millevels.hcrlevel = (v.orighcrlevel/100)*hcrdis
        millevels.save(update_fields=['hcrlevel'])
    if ((v.origdeslevel/100)*desdis) < deslevel:
        update.techlevelchange(deslevel, (v.origdeslevel/100)*desdis, 'destroyers', 5)
        millevels.deslevel = (v.origdeslevel/100)*desdis
        millevels.save(update_fields=['deslevel'])
    if ((v.origfrilevel/100)*fridis) < frilevel:
        update.techlevelchange(frilevel, (v.origfrilevel/100)*fridis, 'frigates', 4)
        millevels.frilevel = (v.origfrilevel/100)*fridis
        millevels.save(update_fields=['frilevel'])
    if ((v.origlcrlevel/100)*lcrdis) < lcrlevel:
        update.techlevelchange(lcrlevel, (v.origlcrlevel/100)*lcrdis, 'light cruisers', 3)
        millevels.lcrlevel = (v.origlcrlevel/100)*lcrdis
        millevels.save(update_fields=['lcrlevel'])
    if ((v.origcorlevel/100)*cordis) < corlevel:
        update.techlevelchange(corlevel, (v.origcorlevel/100)*cordis, 'corvettes', 2)
        millevels.corlevel = (v.origcorlevel/100)*cordis
        millevels.save(update_fields=['corlevel'])


def spyturnchange():
    for spy in Spy.objects.select_related('owner', 'location', 'location__preferences').all().iterator():
        if spy.location != spy.owner:
            if spy.location.preferences.vacation:
                spy.locationreset()
                update.spyvacation(spy.owner)
            else:
                spy.timespent += 1
                spy.save(update_fields=['timespent'])
    return cleanups()


def randomevents(world):

        # Goverment trigger
        if -60 < world.polsystem < -20:
            if random.randint(1,200) <= 2:
                htmldata = news.fleetevent()
                ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=3)

        if world.polsystem <= -60:
            if random.randint(1,200) <= 2:
                htmldata = news.rebeladmiral()
                ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=6)

        # No trigger
        if random.randint(1,200) <= 2:
            htmldata = news.asteroidevent()
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=4)

        if random.randint(1,200) <= 2:
            htmldata = news.durasteroid()
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=8)

        if random.randint(1,200) <= 1:
            htmldata = news.dangerasteroid()
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=5)

        if random.randint(1,200) <= 1:
            htmldata = news.traderaiders()
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=7)

        if random.randint(1,1000) <= 1:
            htmldata = news.fuelexplode()
            if world.warpfuelprod >= 10:
                world.warpfuelprod = F('warpfuelprod') - 10
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=9)

        if random.randint(1,2000) <= 1:
            htmldata = news.xenu()
            ActionNewsItem.objects.create(target=world, content=htmldata, actiontype=10)


def resetsturnchange(world):
        if world.gdp < 250:
            update.gdpreset(world)
        if world.stability < -80:
            outcome = random.randint(1, 2)
            if outcome == 2:
                update.stabreset(world)


def cleanups():
    for anno in Announcement.objects.all().iterator():
        if v.now() > (anno.datetime + datetime.timedelta(days=5)):
            anno.delete()
    for trade in Trade.objects.all().iterator():
        if v.now() > (trade.posted + datetime.timedelta(days=2)):
            update.tradetimeout(trade)
            trade.delete()
    for actionnews in ActionNewsItem.objects.all().iterator():
        if v.now() > (actionnews.datetime + datetime.timedelta(weeks=1)):
            actionnews.delete()
    for mytask in Task.objects.all().iterator():
        if v.now() > (mytask.datetime + datetime.timedelta(weeks=4)):
            mytask.delete()
    for mynews in NewsItem.objects.all().iterator():
        if v.now() > (mynews.datetime + datetime.timedelta(weeks=4)):
            mynews.delete()
    return warcleanup()


def warcleanup():
    for war in War.objects.all().iterator():
        attacktimeout = False
        if v.now() > war.lastattack + datetime.timedelta(hours=36) and v.now() > war.lastattack + datetime.timedelta(hours=36):
            attacktimeout = True
        if v.now() > (war.starttime + datetime.timedelta(weeks=1)) or attacktimeout:
            update.wartimeout(war.attacker, war.defender)
            war.delete()


### Non-periodic tasks


@task
def shipaid(senderpk, recipientpk, taskid, ship, amount, training):
    world = World.objects.get(pk=senderpk)
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    target = World.objects.get(pk=recipientpk)
    tgtfleet = target.preferences.recievefleet
    action = {'add': {ship: amount, 'training': training}}
    utilities.atomic_fleet(tgtfleet.pk, action)
    outcome = "We recieved %s %s from %s at %s" % (amount, 
        shiptype.replace('_', ' ').capitalize(), sender, now())
    Task.objects.filter(pk=taskid).update(outcome=outcome)


@task
def directaid(worldno, targetno, taskid, resources, freighters):
    worlds = World.objects.filter(Q(pk=worldno)|Q(pk=targetno))
    world = worlds.get(pk=worldno)
    target = worlds.get(pk=targetno)
    action = {'freightersinuse': {'action': 'subtract', 'amount': freighters}}
    utilities.atomic_world(worldno, action) #set freighters for sender
    log = ResourceLog.objects.create(owner=target, target=world)
    resource_text = ""
    if len(resources) == 1:
        resource_text = "%s %s" % (resources[0][1], resources[0][0])
        action = {resources[0][0]: {'action': 'add', 'amount': resources[0][1]}}
        Logresource.objects.create(resource=resource[0][0], amount=resource[0][1], log=log)
    else:
        action = {}
        for i, resource in enumerate(resources, 1):
            resource_text += "%s %s" % (resource[1], resource[0])
            if len(resources) - 1 == i:
                resource_text += ' and '
            else:
                resource_text += ', '
            action.update({resources[0]: {'action': 'add', 'amount': resources[1]}})
            Logresource.objects.create(resource=resource[0], amount=resource[1], log=log)
        resource_text = resource_text[:-2]
    utilities.atomic_world(targetno, action) #add to target
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)

    htmldata = news.directaidcompletion(world, resources)
    NewsItem.objects.create(target=target, content=htmldata)

    #utilities.spyintercept(target, world, resources)
    outcome = "We received %s from %s on %s." % (resource_text, fullworld, now())
    Task.objects.filter(pk=taskid).update(outcome=outcome)


@task
def fleetaid(worldpk, targetpk, taskpk, fleetpk, lending=True):
    world = World.objects.get(pk=worldpk)
    targetworld = World.objects.get(pk=targetpk)
    task = Task.objects.get(pk=taskpk)
    transferfleet = fleet.objects.get(pk=fleetpk)
    actions = {'set': {'controller': targetworld, 'sector': targetworld.sector}}
    if lending is False: #recipient is granted ownership
        actions['set'].update({'world': targetworld})
    utilities.atomic_fleet(transferfleet.pk, actions) #sets attributes in a safe way
    htmldata = news.fleetaidcompletion(world, transferfleet.name)
    NewsItem.objects.create(target=target, content=htmldata)
    ResourceLog.objects.create(owner=target, target=world, res=transferfleet.name, amount=1, sent=False, trade=False)
    outcome = "We recieved fleet %s from %s at %s!" % (transferfleet.name, world.name, now())
    task = Task.objects.filter(pk=taskpk).update(outcome=outcome)


@task
def tradecomplete(senderpk, recieverpk, taskid, tradeoffer, total_in, required_freighters):
    sender = World.objects.get(pk=senderpk)
    reciever = World.objects.get(pk=recieverpk)
    senderactions = {
    'freighters': {'action': 'add', 'amount': required_freighters},
    'freightersinuse': {'action': 'subtract', 'amount': required_freighters}
    }
    recieveractions = {tradeoffer: {'action': 'add', 'amount': total_in}}
    utilities.atomic_world(senderpk, senderactions)
    utilities.atomic_world(recieverpk, recieveractions)

    fullworld = '<a href="%s">%s</a>' % (sender.get_absolute_url(), sender.name)

    log = ResourceLog.objects.create(owner=reciever, target=sender, sent=False, trade=True)
    Logresource.objects.create(resource=tradeoffer, log=log, amount=total_in)

    htmldata = news.tradecompletion(sender, tradeoffer, total_in)
    NewsItem.objects.create(target=reciever, content=htmldata)
    #utilities.spyintercept(reciever, sender, actions)
    outcome = "We received %(amount)s %(resource)s from our trade with %(world)s on %(time)s." \
                % {'amount':total_in, 'resource': tradeoffer, 'world':fullworld, 'time':now()}
    Task.objects.filter(pk=taskid).update(outcome=outcome)


@task
def shiptradecomplete(senderpk, recieverpk, taskid, ships, training):
    #ships is a string argument
    recipient = World.objects.get(pk=recieverpk)
    sender = World.objects.get(pk=senderpk)
    recievefleet = recipient.preferences.recievefleet
    if recievefleet.sector != recipient.sector: #if out of sector, reset the choice
        name = recievefleet.name
        recievefleet = recipient.fleets.all().get(sector='hangar')
        recipient.preferences.recievefleet = recievefleet
        recipient.preferences.save()
        NewsItem.objects.create(target=recipient, content="%s is out of sector so incoming ships will be directed to the hangar." % name)
    amount, ship = ships.split(' ')
    log = ResourceLog.objects.create(owner=recipient, target=sender, sent=False, trade=True)
    Logresource.objects.create(resource=ship, log=log, amount=amount)
    actions = {'add': {ship: int(amount), 'training': training}}
    utilities.atomic_fleet(recievefleet.pk, actions)
    htmldata = news.tradecompletionships(sender, ships)
    NewsItem.objects.create(target=recipient, content=htmldata)
    link = '<a href="%s">%s</a>' % (sender.get_absolute_url(), sender.name)
    outcome = "%s has recieved %s from our trade with %s!" % (recievefleet.name, ships, link)

    Task.objects.filter(pk=taskid).update(outcome=outcome)

@task
def fleet_warp(fleetpk, name, sector, taskpk):
    actions = {'set': {'sector': sector}}
    utilities.atomic_fleet(fleetpk, actions)
    outcome="Fleet %s has arrived in sector %s at %s" % (name, sector, now())
    Task.objects.filter(pk=taskpk).update(outcome=outcome)
