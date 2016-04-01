# Django Imports
import django
django.setup()
from celery import task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.db.models import F
from django.core.urlresolvers import reverse

# Python Imports
import random, datetime
import decimal

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

# every 20 min
@periodic_task(run_every=crontab(minute="0,20,40", hour="*", day_of_week="*"))
def addbudget():

    for world in World.not_vacation_objects.all().iterator():
        toadd = update.toadd(world).quantize(D('.1')) # round to 1dp
        cap = update.budgetcap(world)

        if world.budget > cap: # no adding
            pass
        elif D(cap)-D(toadd) <= world.budget <= 3*cap: # set to cap
            world.budget = cap
            world.save(update_fields=['budget'])
        else:
            world.budget = F('budget') + toadd
            world.save(update_fields=['budget'])


# every turn change
@periodic_task(run_every=crontab(minute="1", hour="0,12", day_of_week="*"))
def attributeturnchange():

    for world in World.not_vacation_objects.all().iterator():

        update.tradeavailability(world)

        # Value calculation
        contstab = update.contstab(world)
        contqol = update.contqol(world)
        contreb = update.contreb(world)
        stabcont = update.stabcont(world)
        stabqol = update.stabqol(world)
        stabreb = update.stabreb(world)
        rebstab = update.rebstab(world)
        grotrade, geu = update.grotrade(world, True)
        grostab = update.grostab(world)
        gropol = world.growth

        world.budget = F('budget') + geu
        world.save(update_fields=['budget'])
        world = World.objects.get(pk=world.pk)

        if world.budget < world.industrialprogram:
            underallocated = True
            allocated = world.budget
        else:
            underallocated = False
            allocated = world.industrialprogram

        groind, returned = update.groind(world, allocated)
        groind += update.groindvar(groind)

        # Text generation
        updatelist = []
        updatelist.append(update.contstabnotif(contstab))
        updatelist.append(update.contqolnotif(contqol))
        updatelist.append(update.contrebnotif(contreb))
        updatelist.append(update.stabcontnotif(stabcont))
        updatelist.append(update.stabqolnotif(stabqol))
        updatelist.append(update.stabrebnotif(stabreb))
        updatelist.append(update.rebstabnotif(rebstab))
        updatelist.append(update.growthnotif(int(grotrade), int(grostab), int(gropol), int(groind)))
        updatelist.append(update.groallocnotif(underallocated))

        # Updates
        world.gdp = F('gdp') + grotrade + grostab + gropol + groind
        utilities.contentmentchange(world, (contstab + contreb + contqol))
        utilities.stabilitychange(world, (stabcont + stabqol + stabreb))
        utilities.rebelschange(world, rebstab)
        world.budget = F('budget') - allocated + returned
        world.growth = 0
        Agreement.objects.filter(sender=world).update(available=True)

        world.save(update_fields=['gdp','budget','growth'])

        # Notification
        update.turndetails(world, updatelist)


@periodic_task(run_every=crontab(minute="2", hour="0,12", day_of_week="*"))
def miscturnchange():

    GlobalData.objects.filter(pk=1).update(turnbackground=v.background())

    for world in World.not_vacation_objects.all().iterator():
        # Adding materials
        world.duranium = F('duranium') + world.duraniumprod
        world.tritanium = F('tritanium') + world.tritaniumprod
        world.adamantium = F('adamantium') + world.adamantiumprod

        # Salvage
        world.turnsalvaged = False

        # QoL decay
        change = round((world.qol+140)/float(40))
        utilities.qolchange(world, -change)

        # Other misc stuff
        world.warsperturn = 0
        world.econchanged = False
        world.turnresearched = False
        if world.shipyardsinuse < 0:
            world.shipyardsinuse = 0
        if world.freightersinuse < 0:
            world.freightersinuse = 0
        world.declaredwars.clear()

        world.save(update_fields=['duranium','tritanium','adamantium','warsperturn','econchanged','turnresearched',
            'shipyardsinuse','freightersinuse','turnsalvaged'])


@periodic_task(run_every=crontab(minute="3", hour="0,12", day_of_week="*"))
def militaryturnchange():

    for world in World.not_vacation_objects.all().iterator():
        fuelloss = update.fuelcost(world)

        if world.warpfuel + world.warpfuelprod - fuelloss < 0:
            world.warpfuel = 0
            wearchange = -100
            update.nofuel(world)
        else:
            world.warpfuel = F('warpfuel') + (world.warpfuelprod - fuelloss)
            wearchange = 40

        for region in ['A', 'B', 'C', 'D']:
            utilities.wearinesschange(world, region, wearchange)

        for region in ['A', 'B', 'C', 'D', 'S', 'H']:
            maximum = utilities.trainingfromlist(utilities.regionshiplist(world, region))
            factor = (0.2 if region == 'H' else 0.02)
            utilities.trainingchange(world, region, -int(maximum*factor))

        world.startpower = utilities.militarypower(world, world.region) + utilities.militarypower(world, 'S')
        world.powersent = 0

        world.save(update_fields=['warpfuel','startpower','powersent'])


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


@periodic_task(run_every=crontab(minute="5", hour="0,12", day_of_week="*"))
def spyturnchange():

    for spy in Spy.objects.all().iterator():
        if spy.location != spy.owner:
            if spy.location.vacation:
                spy.locationreset()
                update.spyvacation(spy.owner)
            else:
                spy.timespent += 1
                spy.save(update_fields=['timespent'])


@periodic_task(run_every=crontab(minute="6", hour="0,12", day_of_week="*"))
def randomevents():

    for world in World.not_vacation_objects.all().iterator():

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


@periodic_task(run_every=crontab(minute="7", hour="0,12", day_of_week="*"))
def resetsturnchange():

    for world in World.not_vacation_objects.all().iterator():
        if world.gdp < 250:
            update.gdpreset(world)
        if world.stability < -80:
            outcome = random.randint(1, 2)
            if outcome == 2:
                update.stabreset(world)


@periodic_task(run_every=crontab(minute="8", hour="0", day_of_week="*"))
def loginmultidetect():
    multiloginlist = {}
    for world in World.objects.all().iterator():
        try:
            multiloginlist[world.lastloggedinip].append(world.worldid)
        except KeyError:
            multiloginlist[world.lastloggedinip] = [world.worldid]
    update.multidetect(multiloginlist, 'Login')


@periodic_task(run_every=crontab(minute="9", hour="0", day_of_week="*"))
def cleanups():
    for anno in Announcement.objects.all().iterator():
        if v.now() > (anno.datetime + datetime.timedelta(days=5)):
            anno.delete()
    for trade in Trade.objects.all().iterator():
        if v.now() > (trade.datetime + datetime.timedelta(days=2)):
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


@periodic_task(run_every=crontab(minute="10", hour="0", day_of_week="*"))
def warcleanup():
    for war in War.objects.all().iterator():
        attacktimeout = False
        if v.now() > war.timetonextattack + datetime.timedelta(hours=36) and v.now() > war.timetonextattack + datetime.timedelta(hours=36):
            attacktimeout = True
        if v.now() > (war.starttime + datetime.timedelta(weeks=1)) or attacktimeout:
            attacker = war.attacker
            defender = war.defender
            war.delete()
            update.wartimeout(attacker, defender)


@periodic_task(run_every=crontab(minute="11", hour="0,12", day_of_week="*"))
def gdpthresholdreset():
    for world in World.not_vacation_objects.all().iterator():
        sale, created = GDPSaleThresholdManager.objects.update_or_create(target=world, defaults={"sellthreshold": world.gdp*0.25, "buythreshold": world.gdp*0.5})


@periodic_task(run_every=crontab(minute="59", hour="23", day_of_week="sun"))
def lotterywinner():
    tochoice = LotteryTicket.objects.all()
    if len(tochoice) == 0:
        winner = World.objects.get(worldid=1)
    else:
        winning = random.choice(LotteryTicket.objects.all())
        winner = winning.owner
    prizepot = len(tochoice)*75 + 200

    winner.budget = F('budget') + prizepot
    winner.save(update_fields=['budget'])

    newstext = "Well done, %s! You're the lucky winner of the galactic lottery, with a prize pot of %s GEU!" % (winner.user_name, prizepot)
    NewsItem.objects.create(target=winner, content=newstext)

    LotteryTicket.objects.all().delete()

    GlobalData.objects.filter(pk=1).update(lotterywinnerid=winner.worldid, lotterywinneramount=prizepot)


### Non-periodic tasks

@task
def buildfreighter(worldno, taskid, amount):
    world = World.objects.get(worldid=worldno)

    if world.shipyardsinuse - 2*amount < 0:
        world.shipyardsinuse = 0
    else:
        world.shipyardsinuse = F('shipyardsinuse') - 2*amount
    world.save(update_fields=['shipyardsinuse'])

    if 'prodstaging' in world.shipsortprefs:
        destination = 'staging area'
        utilities.freightermove(world, 'S', amount)
    else:
        destination = 'home fleet'
        utilities.freightermove(world, world.region, amount)

    pluralise = ("freighter was" if amount == 1 else "%s freighters were" % amount)

    task = Task.objects.get(pk=taskid)
    task.outcome = "Your %s completed and delivered to your %s on %s." % (pluralise, destination, now())
    task.save()


@task
def buildship(worldno, taskid, shiptype, amount, yards):
    world = World.objects.get(worldid=worldno)

    if world.shipyardsinuse - yards*amount < 0:
        world.shipyardsinuse = 0
    else:
        world.shipyardsinuse = F('shipyardsinuse') - yards*amount
    world.save(update_fields=['shipyardsinuse'])

    if 'prodstaging' in world.shipsortprefs:
        destination = 'staging area'
        utilities.movecomplete(world, shiptype, amount, 'S', 0)
    else:
        destination = 'home fleet'
        utilities.movecomplete(world, shiptype, amount, world.region, 0)

    name = utilities.resname(shiptype+10, amount, lower=True)

    pluralise = ("%s was" % name if amount == 1 else "%s %s were" % (amount, name))

    task = Task.objects.get(pk=taskid)
    task.outcome = "Your %s completed and delivered to your %s on %s." % (pluralise, destination, now())
    task.save()


@task
def buildpersonalship(worldno, taskid, shiptype):
    world = World.objects.get(worldid=worldno)

    world.shipyardsinuse = F('shipyardsinuse') - 5
    world.flagshiptype = shiptype
    world.flagshiplocation = world.region

    if shiptype == 1:
        world.flagshippicture = 'pf01'
    elif shiptype == 2:
        world.flagshippicture = 'my01'
    elif shiptype == 3:
        world.flagshippicture = 'cs01'

    world.save(update_fields=['shipyardsinuse', 'flagshiptype', 'flagshiplocation','flagshippicture'])

    name = display.personalshipname(shiptype)

    task = Task.objects.get(pk=taskid)
    task.outcome = "Your %s was completed and delivered to your home fleet on %s." % (name, now())
    task.save()

    try:
        world.flagshipbuild = False
        world.save(update_fields=['flagshipbuild'])
    except:
        pass


@task
def moveship(worldno, taskid, amount, shiptype, shiptext, regionfrom, regionto, fuelcost, trainingchange):
    world = World.objects.get(worldid=worldno)
    try:
        task = Task.objects.get(pk=taskid)
    except:
        pass # revoked
    else:
        fromname = display.region_display(regionfrom)
        toname = display.region_display(regionto)
        movecheck = utilities.movecheck(world, shiptype, amount, regionfrom)
        if not movecheck:
            htmldata = "Your attempt to warp %s %s from %s to %s failed as you did not have enough ships." \
                        % (amount, shiptext, regionfrom, regionto)
            NewsItem.objects.create(target=world, content=htmldata)
            task.outcome = "You did not have enough ships to warp %(amount)s %(ship)s from %(from)s to %(to)s!" \
                        % {'amount':amount, 'ship':shiptext, 'from':fromname, 'to':toname}
        elif world.warpfuel < fuelcost:
            htmldata = "Your attempt to warp %s %s from %s to %s failed as you did not have enough fuel." \
                        % (amount, shiptext, regionfrom, regionto)
            NewsItem.objects.create(target=world, content=htmldata)
            task.outcome = "You did not have enough fuel to warp %(amount)s %(ship)s from %(from)s to %(to)s!" \
                        % {'amount':amount, 'ship':shiptext, 'from':fromname, 'to':toname}
        else:
            attloss = ''
            world.warpfuel = F('warpfuel') - fuelcost
            if world.wardefender.count() > 0 and regionfrom == world.region:
                utilities.contentmentchange(world, -10)
                utilities.stabilitychange(world, -5)
                attloss = 'You were in a defensive war, and you lost perception and stability by sending ships away from your home!'
            world.save(update_fields=['warpfuel'])
            utilities.movecomplete(world,shiptype,-amount,regionfrom,-trainingchange)
            utilities.movecomplete(world,shiptype,amount,regionto,trainingchange)

            task.outcome = "Your %(amount)s %(ship)s warped from %(from)s to %(to)s on %(time)s. %(att)s" \
                        % {'amount':amount, 'ship':shiptext, 'from':fromname, 'to':toname, 'time':now(), 'att':attloss}

        task.save()


@task
def movepersonalship(worldno, taskid, regionfrom, regionto):
    world = World.objects.get(worldid=worldno)
    try:
        task = Task.objects.get(pk=taskid)
    except:
        pass
    else:
        fromname = display.region_display(regionfrom)
        toname = display.region_display(regionto)
        check = (True if world.flagshiptype != 0 else False)
        if not check:
            htmldata = "Your personal ship was destroyed before it could warp from %s to %s!" % (fromname, toname)
            NewsItem.objects.create(target=world, content=htmldata)
            task.outcome = "Your personal ship was destroyed before it could warp from %s to %s!" % (fromname, toname)
        elif world.warpfuel < 5:
            htmldata = news.notenoughpersonal(amount, shiptext, fromname, toname, 'fuel')
            NewsItem.objects.create(target=world, content=htmldata)
            task.outcome = "You did not have enough fuel to warp your personal ship from %s to %s!" % (fromname, toname)
        else:
            attloss = ''
            world.warpfuel = F('warpfuel') - 5
            world.flagshiplocation = regionto
            if world.wardefender.count() > 0 and regionfrom == world.region:
                utilities.contentmentchange(world, -10)
                utilities.stabilitychange(world, -5)
                attloss = 'You were in a defensive war, and you lost perception and stability by sending ships away from your home!'
            world.save(update_fields=['warpfuel','flagshiplocation'])

            task.outcome = "Your personal ship warped from %(from)s to %(to)s on %(time)s. %(att)s" \
                        % {'from':fromname, 'to':toname, 'time':now(), 'att':attloss}

        task.save()


@task
def movefreighter(worldno, taskid, amount, regionfrom, regionto):
    world = World.objects.get(worldid=worldno)
    try:
        task = Task.objects.get(pk=taskid)
    except:
        pass
    else:
        fromname = display.region_display(regionfrom)
        toname = display.region_display(regionto)
        movecheck = utilities.freightercheck(world, regionfrom, amount)
        if not movecheck:
            htmldata = news.notenough(amount, 'freighters', fromname, toname, 'of them')
            NewsItem.objects.create(target=world, content=htmldata)
            task.outcome = "You did not have enough freighters to warp %(amount)s of them from %(from)s to %(to)s!" \
                        % {'amount':amount, 'from':fromname, 'to':toname}
        else:
            utilities.freightermove(world, regionfrom, -amount)
            utilities.freightermove(world, regionto, amount)

            task.outcome = "Your %(amount)s freighters warped from %(from)s to %(to)s on %(time)s." \
                        % {'amount':amount, 'from':fromname, 'to':toname, 'time':now()}

        task.save()


@task
def mothball(worldno, taskid, amount, shiptype, shiptext, fuelcost, trainingchange, direction):
    world = World.objects.get(worldid=worldno)
    try:
        task = Task.objects.get(pk=taskid)
    except:
        pass
    else:
        if direction == 'plus':
            if 'sendstaging' in world.shipsortprefs:
                movecheck = utilities.movecheck(world, shiptype, amount, 'S')
            else:
                movecheck = utilities.movecheck(world, shiptype, amount, world.region)
            if not movecheck:
                htmldata = news.mothball(amount, shiptext, 'ships', 'plus')
                newsitem = NewsItem(target=world, content=htmldata)
                newsitem.save()
                task.outcome = "You did not have enough ships to mothball %s %s!" % (amount, shiptext)
            else:
                attloss = ''
                if world.wardefender.count() > 0:
                    utilities.contentmentchange(world, -10)
                    utilities.stabilitychange(world, -5)
                    attloss = 'You were in a defensive war and your have lost perception and stability by mothballing ships!'

                if 'sendstaging' in world.shipsortprefs:
                    utilities.movecomplete(world,shiptype,-amount,'S',-trainingchange)
                else:
                    utilities.movecomplete(world,shiptype,-amount,world.region,-trainingchange)
                utilities.movecomplete(world,shiptype,amount,'H',trainingchange)

                task.outcome = "Your %(amount)s %(ship)s successfully entered orbital hangars on %(time)s. %(att)s" \
                            % {'amount':amount, 'ship':shiptext, 'time':now(), 'att':attloss}

        if direction == 'minus':
            movecheck = utilities.movecheck(world, shiptype, amount, 'H')
            if not movecheck:
                htmldata = news.mothball(amount, shiptext, 'ships', 'minus')
                NewsItem.objects.create(target=world, content=htmldata)
                task.outcome = "You did not have enough ships to mothball %s %s!" % (amount, shiptext)
            elif world.warpfuel < fuelcost:
                htmldata = news.mothball(amount, shiptext, 'fuel', 'minus')
                NewsItem.objects.create(target=world, content=htmldata)
                task.outcome = "You did not have enough fuel for your %s %s to re-enter active service!" % (amount, shiptext)
            else:
                world.warpfuel = F('warpfuel') - fuelcost
                world.save(update_fields=['warpfuel'])
                utilities.movecomplete(world,shiptype,-amount,'H',-trainingchange)
                if 'receivestaging' in world.shipsortprefs:
                    utilities.movecomplete(world,shiptype,amount,'S',trainingchange)
                else:
                    utilities.movecomplete(world,shiptype,amount,world.region,trainingchange)

                task.outcome = "Your %(amount)s %(ship)s successfully re-entered active service in the home fleet on %(time)s." \
                            % {'amount':amount, 'ship':shiptext, 'time':now()}

        task.save()


@task
def directaid(worldno, targetno, taskid, send, sendamount, trainingchange, freighters):
    world = World.objects.get(worldid=worldno)
    target = World.objects.get(worldid=targetno)
    utilities.resourcecompletion(target, send, sendamount, trainingchange)

    world.freightersinuse = F('freightersinuse') - freighters
    world.save(update_fields=['freightersinuse'])
    utilities.freightermove(world, world.region, freighters)

    resname = utilities.resname(send, sendamount)

    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':world.world_name}

    ResourceLog.objects.create(owner=target, target=world, res=send, amount=sendamount, sent=False, trade=False)

    htmldata = news.directaidcompletion(world, resname, sendamount)
    NewsItem.objects.create(target=target, content=htmldata)

    utilities.spyintercept(target, world, resname, sendamount)

    task = Task.objects.get(pk=taskid)
    task.outcome = "We received %(amount)s %(name)s from %(world)s on %(time)s." \
                % {'amount':sendamount, 'name':resname, 'world':fullworld, 'time':now()}
    task.save()


@task
def tradecomplete(worldno, targetno, taskid, send, sendamount, trainingchange, freighters):
    world = World.objects.get(worldid=worldno)
    target = World.objects.get(worldid=targetno)
    utilities.resourcecompletion(target, send, sendamount, trainingchange)

    world.freightersinuse = F('freightersinuse') - freighters
    world.save(update_fields=['freightersinuse'])
    utilities.freightermove(world, world.region, freighters)

    resname = utilities.resname(send, sendamount)

    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':world.world_name}

    ResourceLog.objects.create(owner=target, target=world, res=send, amount=sendamount, sent=False, trade=True)

    htmldata = news.tradecompletion(world, resname, sendamount)
    NewsItem.objects.create(target=target, content=htmldata)

    utilities.spyintercept(target, world, resname, sendamount)

    task = Task.objects.get(pk=taskid)
    task.outcome = "We received %(amount)s %(name)s from our trade with %(world)s on %(time)s." \
                % {'amount':sendamount, 'name':resname, 'world':fullworld, 'time':now()}
    task.save()
