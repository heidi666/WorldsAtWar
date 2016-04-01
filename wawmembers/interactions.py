# Django Imports
from django.db.models import F
from django.shortcuts import redirect, render
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import random, decimal
import datetime as time

# WaW Imports
from wawmembers.models import *
from wawmembers.forms import *
from wawmembers.loggers import aidlogger
import wawmembers.tasks as newtask
import wawmembers.display as display
import wawmembers.outcomes_policies as outcomes
import wawmembers.newsgenerator as news
import wawmembers.taskgenerator as taskdata
import wawmembers.utilities as utilities
import wawmembers.variables as v

'''
Everything that deals with one world interacting with another. Wars, attacks, spies, etc.
'''

D = decimal.Decimal


def stats_ind(request, userid):
    'Displays information about other worlds.'

    # redirects
    if request.user.is_authenticated() and int(userid) == int(request.user.id):
        return redirect('main') # redirect to your own page

    try:
        target = World.objects.get(worldid=userid)
    except ObjectDoesNotExist:
        return render(request, 'notfound.html', {'item': 'world'}) # instead of 404

    if target.worldid == 0:
        return render(request, 'notfound.html', {'item': 'world'}) # dummy deleted world

    # variable setup
    message = atwar = haswars = offlist = deflist = admin = None
    warprotection = gdpprotection = targetprotection = None
    peaceoffer = warfuelcost = raidcost = None
    displayactions = costforgeuaid = indefwar = None
    nospies = spyintarget = spyform = spyintel = timeforintel = None
    aidform = traderessend = sendtrade = receivetrade = None
    defaultopen = 'domestic,economic,diplomacy,military'

    alliance = target.alliance

    displaybuilds = [False for i in range(9)]
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()

    # military levels setup
    if target.millevel >= drelevel:
        limit = 9
        millevel = 'Dreadnought'
        progress = None
    elif target.millevel >= bshlevel:
        limit = 9
        millevel = 'Battleship'
        progress = (target.millevel - bshlevel)/float(drelevel - bshlevel)
    elif target.millevel >= bcrlevel:
        limit = 8
        millevel = 'Battlecruiser'
        progress = (target.millevel - bcrlevel)/float(bshlevel - bcrlevel)
    elif target.millevel >= hcrlevel:
        limit = 7
        millevel = 'Heavy Cruiser'
        progress = (target.millevel - hcrlevel)/float(bcrlevel - hcrlevel)
    elif target.millevel >= frilevel:
        limit = 6
        millevel = 'Frigate'
        progress = (target.millevel - frilevel)/float(hcrlevel - frilevel)
    elif target.millevel >= deslevel:
        limit = 5
        millevel = 'Destroyer'
        progress = (target.millevel - deslevel)/float(frilevel - deslevel)
    elif target.millevel >= lcrlevel:
        limit = 4
        millevel = 'Light Cruiser'
        progress = (target.millevel - lcrlevel)/float(deslevel - lcrlevel)
    elif target.millevel >= corlevel:
        limit = 3
        millevel = 'Corvette'
        progress = (target.millevel - corlevel)/float(lcrlevel - corlevel)
    else:
        limit = 2
        millevel = 'Fighter'
        progress = target.millevel/float(corlevel)
    for index, value in enumerate(displaybuilds[:limit]):
        displaybuilds[index] = True

    if progress is not None:
        progress = int(100*progress/5.0)*5

    # region ship lists
    homeregion, staging, region1, region2, region3, hangars = utilities.mildisplaylist(target)

    shiploc = display.region_display(target.flagshiplocation)

    try:
        world = World.objects.get(worldid=request.user.id)
        if world.vacation:
            raise Exception # not allowed to take actions when you're on vacation
    except:
        pass
    else:
        displayactions = True
        defaultopen = world.statsopenprefs

        # war status
        if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
            atwar = True
            war = War.objects.get(attacker=world, defender=target)
            if war.peaceofferbyatk is not None:
                peaceoffer = True
        elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
            atwar = True
            war = War.objects.get(attacker=target, defender=world)
            if war.peaceofferbydef is not None:
                peaceoffer = True

        if abs(world.econsystem - target.econsystem) == 2:
            costforgeuaid = True

        if world.wardefender.count() > 0:
            indefwar = True

        # if you have spare resources
        if world.resourceproduction - Agreement.objects.filter(sender=world).exclude(receiver=world).count() > 0:
            traderessend = True

        # trade agreements
        if Agreement.objects.filter(sender=world, receiver=target).exists():
            sendtrade = True
        if Agreement.objects.filter(sender=target, receiver=world).exists():
            receivetrade = True

        # convenience admin links
        if world.worldid == 1:
            admin = True

        if request.method == 'POST':
            form = request.POST

            if "sendcomm" in form:
                commdata = form['comm']
                if len(commdata) > 500:
                    message = 'Maximum 500 characters!'
                elif len(commdata) == 0:
                    message = 'You cannot send an empty comm!'
                elif '<' in commdata or '>' in commdata:
                    message = 'The comm contains invalid characters!'
                else:
                    Comm.objects.create(target=target, sender=world, content=commdata)
                    SentComm.objects.create(target=target, sender=world, content=commdata)
                    message = 'Communique sent.'

            if "wardec" in form:
                power = utilities.militarypowerwfuel(world, target.region)
                ownpower = utilities.powerallmodifiers(world, target.region)
                targetpower = utilities.powerallmodifiers(target, target.region, ignorefuel=True) + \
                  utilities.powerallmodifiers(target, 'S', ignorefuel=True)
                if target.vacation:
                    message = 'This world is in vacation mode. You cannot declare war on it.'
                elif power == 0:
                    message = 'You cannot declare war with no fleet power!'
                elif atwar:
                    message = 'You are already at war with this world!'
                elif target in world.declaredwars.all():
                    message = 'You have already warred this world recently!'
                elif world.warsperturn == 3:
                    message = 'You have declared too many wars recently! Your logistics division needs time to organise the fleet.'
                elif v.now() < (target.creationtime + time.timedelta(weeks=1)) and (target.noobprotect):
                    message = 'You cannot declare war on a world that has only just joined the galaxy!'
                elif v.now() < target.warprotection:
                    message = 'Your generals refuse to attack this world which has recently lost a war! Their honour is at stake.'
                elif (target.gdp < 0.75*(world.gdp)) and (v.now() > target.abovegdpprotection):
                    message = 'Your fleet refuses to attack such a puny world!'
                elif target.wardefender.count() == 3:
                    message = 'Your fleet refuses to attack a world under such siege!'
                elif world.warattacker.count() == 3:
                    message = 'Your fleet refuses to divide its attentions any further!'
                elif ownpower < 0.1*targetpower:
                    message = 'Your fleet refuses to declare war on such a mighty enemy!'
                elif len(form['warreason']) > 20:
                    message = 'Your war declaration message is too long.'
                else:
                    endprotect = ''
                    aboveprotect = ''
                    warreason = form['warreason']
                    if v.now() < world.warprotection:
                        world.warprotection = v.now()
                        world.brokenwarprotect = v.now() + time.timedelta(days=1)
                        world.noobprotect = False
                        world.save(update_fields=['warprotection','brokenwarprotect','noobprotect'])
                        endprotect = '<br>Your war protection is now over, and you may not regain it for 24 hours!'

                    if target.gdp > 3 * world.gdp:
                        world.abovegdpprotection = v.now() + time.timedelta(days=5)
                        world.save(update_fields=['abovegdpprotection'])
                        aboveprotect = '<br>Other worlds of any GDP may attack you, for 5 days.'

                    War.objects.create(attacker=world, defender=target, region=target.region, reason=warreason)

                    htmldata = news.wardec(world,warreason)
                    NewsItem.objects.create(target=target, content=htmldata)

                    world.declaredwars.add(target)
                    world.warsperturn = F('warsperturn') + 1
                    world.save(update_fields=['warsperturn'])
                    message = 'You have declared WAR!' + endprotect + aboveprotect

            if "attack" in form and atwar is None:
                message = 'You are not at war with this world!'
            elif "attack" in form:
                power = utilities.militarypowerwfuel(world, war.region)
                fuelcost = utilities.warpfuelcost(utilities.regionshiplist(world, war.region))
                if utilities.noweariness(world, war.region, 25):
                    message = 'Your fleet is too exhausted to attack!'
                elif power == 0:
                    message = 'You have no fleet power to attack with!'
                elif world.warpfuel < fuelcost:
                    message = 'You do not have enough warpfuel to support this attack!'
                elif world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True) and war.timetonextattack > v.now():
                    timedifference = war.timetonextattack - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True) and war.timetonextdefense > v.now():
                    timedifference = war.timetonextdefense - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                else:
                    if world in War.objects.filter(defender=target) and v.now() < world.warprotection:
                        world.warprotection = v.now()
                        world.save(update_fields=['warprotection'])

                    if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        war.timetonextattack = v.now() + time.timedelta(hours=8)
                    elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        war.timetonextdefense = v.now() + time.timedelta(hours=8)
                    war.save()

                    utilities.wearinesschange(world, war.region, -25)

                    world.warpfuel = F('warpfuel') - fuelcost
                    world.save(update_fields=['warpfuel'])
                    world = World.objects.get(pk=world.pk)

                    return attack(request, world, target, war)

             # freighter raid
            if "raid" in form and atwar is None:
                message = 'You are not at war with this world!'
            elif "raid" in form:
                power = utilities.militarypowerwfuel(world, war.region)
                raidlist = utilities.regionshiplist(world, war.region)[:2] + [0, 0, 0, 0, 0, 0, 0]
                raidcost = utilities.warpfuelcost(raidlist)
                if utilities.noweariness(world, war.region, 5):
                    message = 'Your fleet is too exhausted to raid!'
                elif power == 0:
                    message = 'You do not have a fleet to attack with!'
                elif world.warpfuel < raidcost:
                    message = 'You do not have enough warpfuel to support this attack!'
                elif world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True) and war.timetonextattack > v.now():
                    timedifference = war.timetonextattack - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True) and war.timetonextdefense > v.now():
                    timedifference = war.timetonextdefense - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                else:
                    if world in War.objects.filter(defender=target) and v.now() < world.warprotection:
                        world.warprotection = v.now()
                        world.save(update_fields=['warprotection'])

                    if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        war.timetonextattack = v.now() + time.timedelta(hours=8)
                    elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        war.timetonextdefense = v.now() + time.timedelta(hours=8)
                    war.save()

                    utilities.wearinesschange(world, war.region, -5)

                    world.warpfuel = F('warpfuel') - raidcost
                    world.save(update_fields=['warpfuel'])
                    world = World.objects.get(pk=world.pk)

                    return raid(request, world, target, war)

            if 'offerpeace' in form:
                if atwar is None:
                    message = 'You are not at war with this world!'
                else:
                    htmldata = news.offerpeace(world, target)
                    newsitem = ActionNewsItem(target=target, content=htmldata, actiontype=1)
                    newsitem.save()

                    if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        war.peaceofferbyatk = newsitem
                    elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        war.peaceofferbydef = newsitem
                    war.save()

                    message = 'An offer of peace has been sent, which your enemy will have to accept.'

            if 'revokepeace' in form:
                if atwar is None:
                    message = 'You are not at war with this world!'
                else:
                    htmldata = news.peacerevoke(world)
                    NewsItem.objects.create(target=target, content=htmldata)

                    if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        try:
                            war.peaceofferbyatk.delete()
                        except: pass
                    elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        try:
                            war.peaceofferbydef.delete()
                        except: pass

                    peaceoffer = None
                    message = 'You have revoked your peace offer.'

            if 'directaid' in form:
                form = DirectAidForm(world.millevel, target.millevel, request.POST)
                if world.gdp < 250:
                    message = 'Your world\'s economy is too weak to support your humanitarian efforts!'
                elif form.is_valid():
                    data = form.cleaned_data
                    ressend = data['send']
                    amountsend = int(data['amountsend'])

                    geucost = (D(0.05*amountsend) if costforgeuaid else 0)

                    if ressend == 0:
                        amountsend += geucost

                    amountcheck = utilities.tradeamount(world, ressend, amountsend)
                    shipowncheck = utilities.tradeshiptech(world, ressend)
                    shipothercheck = utilities.tradeshiptech(target, ressend)
                    shippowercheck = utilities.tradeshippower(world, ressend, amountsend)
                    defwarcheck = utilities.shippowerdefwars(world, ressend)
                    count, countcheck = utilities.freightertradecheck(world, ressend, amountsend)
                    if amountsend <= 0:
                        message = 'Enter a positive number.'
                    elif ressend not in v.resources:
                        message = 'Enter a valid resource.'
                    elif amountcheck is not True:
                        message = amountcheck
                    elif shipowncheck is not True:
                        message = shipowncheck
                    elif shipothercheck is not True:
                        message = 'Their fleet does have the knowledge to operate or maintain such ships!'
                    elif shippowercheck is not True:
                        message = shippowercheck
                    elif defwarcheck is not True:
                        message = defwarcheck
                    elif countcheck is not True:
                        message = countcheck
                    else:
                        endprotect = ''
                        attloss = ''
                        resname = utilities.resname(ressend, amountsend, lower=True)
                        if 11 <= ressend <= 19: # ships
                            if v.now() < world.warprotection:
                                world.warprotection = v.now()
                                world.noobprotect = False
                                world.save(update_fields=['warprotection','noobprotect'])
                                endprotect = '<br>Your war protection is now over.'

                            delay = (4 if world.region == target.region else 8)

                            if indefwar:
                                utilities.contentmentchange(world, -10)
                                utilities.stabilitychange(world, -5)
                                attloss = '<br>You have lost perception and stability.'

                            outcometime = v.now() + time.timedelta(hours=delay)
                            if 'sendhome' in world.shipsortprefs:
                                trainingchange = utilities.trainingchangecalc(world, world.region, int(ressend)-10, amountsend)
                            else:
                                trainingchange = utilities.trainingchangecalc(world, 'S', int(ressend)-10, amountsend)

                            taskdetails = taskdata.directaidarrival(world, resname, amountsend)
                            task = Task(target=target, content=taskdetails, datetime=outcometime)
                            task.save()

                            newtask.directaid.apply_async(args=(world.worldid, target.worldid, task.pk, ressend, amountsend,
                                trainingchange, 0), eta=outcometime)

                        elif ressend == 0: # money
                            trainingchange = 0
                            htmldata = news.directaidcompletion(world, resname, amountsend)
                            NewsItem.objects.create(target=target, content=htmldata)
                            utilities.resourcecompletion(target, ressend, amountsend, trainingchange)
                            utilities.spyintercept(target, world, 'GEU', amountsend)
                            ResourceLog.objects.create(owner=target, target=world, res=ressend, amount=amountsend, sent=False, trade=False)

                        else: # resources
                            delay = (1 if world.region == target.region else 2)

                            outcometime = v.now() + time.timedelta(hours=delay)
                            trainingchange = 0

                            world.freightersinuse = F('freightersinuse') + count
                            world.save(update_fields=['freightersinuse'])

                            taskdetails = taskdata.directaidarrival(world, resname, amountsend)
                            task = Task(target=target, content=taskdetails, datetime=outcometime)
                            task.save()

                            newtask.directaid.apply_async(args=(world.worldid, target.worldid, task.pk, ressend, amountsend, trainingchange,
                                count), eta=outcometime)

                        utilities.resourcecompletion(world, ressend, -amountsend, -trainingchange)
                        utilities.freightermove(world, world.region, -count)
                        utilities.spyinterceptsend(world, target, resname, amountsend)

                        ResourceLog.objects.create(owner=world, target=target, res=ressend, amount=amountsend, sent=True, trade=False)

                        aidlogger.info('---')
                        aidlogger.info('%s (id=%s) sent %s %s to %s (id=%s)',
                            world.world_name, world.worldid, amountsend, utilities.resname(ressend), target.world_name, target.worldid)

                        message = 'Aid sent!' + endprotect + attloss

                else:
                    form = DirectAidForm(world.millevel, target.millevel).as_table()

            if "infiltrate" in form:
                form = SelectSpyForm(world, request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    spyid = data['spyselect']
                    try:
                        spy = Spy.objects.get(pk=spyid)
                    except:
                        message = "There is no such spy!"
                    else:
                        if target.vacation:
                            message = 'This world is in vacation mode. You cannot infiltrate it.'
                        elif spy.owner != world:
                            message = "This spy does not belong to your intelligence services!"
                        elif Spy.objects.filter(owner=world, location=target).exists():
                            message = "You already have a spy in this world!"
                        elif spy.location != world:
                            message = "This spy is not at your home world!"
                        elif spy.nextaction > v.now():
                            message = "This spy is currently recovering and unavailable for missions."
                        else:
                            message = infiltrate(spy, target)

            if "propaganda" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 250:
                        message = outcomes.nomoney()
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 250
                        world.save(update_fields=['budget'])
                        message = propaganda(spy, target)

            if "gunrun" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.millevel < 1000:
                        message = outcomes.gunrun('NoTech')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.millevel = F('millevel') - 1000
                        world.save(update_fields=['millevel'])
                        message = gunrun(spy, target)

            if "intel" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 200:
                        message = outcomes.nomoney()
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 200
                        world.save(update_fields=['budget'])
                        message = intel(spy, target)

            if "sabyard" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    elif target.shipyards - target.shipyardsinuse == 0:
                        message = outcomes.sabotage('NoFreeYards')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabyard(spy, target)

            if "sabfuel" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    elif target.warpfuelprod < 10:
                        message = outcomes.sabotage('NoFuelProd')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabfuel(spy, target)

            if "sabdur" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    elif target.duraniumprod < 5:
                        message = outcomes.sabotage('NoDurProd')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabdur(spy, target)

            if "sabtrit" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    elif target.tritaniumprod < 2:
                        message = outcomes.sabotage('NoTritProd')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabtrit(spy, target)

            if "sabadam" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    elif target.adamantiumprod < 1:
                        message = outcomes.sabotage('NoAdamProd')
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabadam(spy, target)

            if "sabhangars" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable for missions."
                    elif world.budget < 2000:
                        message = outcomes.nomoney()
                    else:
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.save(update_fields=['nextaction'])
                        world.budget = F('budget') - 2000
                        world.save(update_fields=['budget'])
                        message = sabhangars(spy, target)

            if "withdraw" in form:
                try:
                    spy = Spy.objects.get(owner=world, location=target)
                except ObjectDoesNotExist:
                    message = "You have no spy in this world!"
                else:
                    if spy.nextaction > v.now():
                        message = "This spy is currently recovering and unavailable."
                    else:
                        spy.inteltime = v.now()
                        spy.location = spy.owner
                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        spy.timespent = 0
                        spy.save()
                        message = 'You have successfully withdrawn your spy from the enemy world!'

            if "sendtraderes" in form:
                if world.resource == target.resource:
                    message = 'This world has the same trade resource as you.'
                elif abs(world.econsystem - target.econsystem) == 2:
                    message = 'You cannot trade with a world that has an opposite economic alignment!'
                elif not traderessend:
                    message = 'You do not have surplus to send!'
                elif Agreement.objects.filter(receiver=target, resource=world.resource).count() > 12:
                    message = 'This world is already receiving too much of your resource!'
                elif sendtrade:
                    message = 'You are already sending your trade resource to this world!'
                else:
                    agreement = list(Agreement.objects.filter(sender=world, receiver=world))[0]
                    agreement.receiver = target
                    agreement.save(update_fields=['receiver'])
                    AgreementLog.objects.create(owner=target, target=world, resource=world.resource, logtype=0)
                    message = 'You are now sending one lot of your trade resource to this world.'

            if "revoketraderes" in form and sendtrade:
                agreement = Agreement.objects.get(sender=world, receiver=target)
                agreement.receiver = world
                agreement.save(update_fields=['receiver'])
                AgreementLog.objects.create(owner=target, target=world, resource=world.resource, logtype=1)
                message = 'You have stopped sending your trade resource to this world.'

            if "refusetraderes" in form and receivetrade:
                agreement = Agreement.objects.get(sender=target, receiver=world)
                agreement.receiver = target
                agreement.save(update_fields=['receiver'])
                AgreementLog.objects.create(owner=target, target=world, resource=world.resource, logtype=3)
                message = 'You have refused this world\'s trade agreement.'

        if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True):
            atwar = True
            war = War.objects.get(attacker=world, defender=target)
            if war.peaceofferbyatk is not None:
                peaceoffer = True
        elif world.worldid in War.objects.filter(attacker=target).values_list('defender', flat=True):
            atwar = True
            war = War.objects.get(attacker=target, defender=world)
            if war.peaceofferbydef is not None:
                peaceoffer = True

        aidform = DirectAidForm(world.millevel, target.millevel).as_table()
        spyform = SelectSpyForm(world)

        # recalculate variables in case an action has changed them
        if v.now() < world.warprotection:
            warprotection = True
        if target.gdp > 3 * world.gdp:
            gdpprotection = True

        if v.now() < target.warprotection:
            targetprotection = True

        if Spy.objects.filter(owner=world, location=world).count() == 0:
            nospies = True

        if Agreement.objects.filter(sender=world, receiver=target).exists():
            sendtrade = True

        if Agreement.objects.filter(sender=target, receiver=world).exists():
            receivetrade = True

        if Spy.objects.filter(owner=world).filter(location=target).count() == 1:
            spyintarget = Spy.objects.filter(owner=world, location=target)[0]
            if spyintarget.inteltime > v.now():
                spyintel = True
                timediff = spyintarget.inteltime - v.now()
                hours, minutes, seconds = utilities.timedeltadivide(timediff)
                timeforintel = 'You have %s:%s:%s of intel remaining.' % (hours, minutes, seconds)

    target = World.objects.get(pk=target.pk)
    homeregion, staging, region1, region2, region3, hangars = utilities.mildisplaylist(target)
    if target.warattacker.count() > 0 or target.wardefender.count() > 0:
        haswars = True
        offlist = [wars.defender for wars in target.warattacker.all()]
        deflist = [wars.attacker for wars in target.wardefender.all()]

    if atwar:
        shiplist = utilities.regionshiplist(world, war.region)
        warfuelcost = utilities.warpfuelcost(shiplist)
        raidlist = shiplist[:2] + [0, 0, 0, 0, 0, 0, 0]
        raidcost = utilities.warpfuelcost(raidlist)

    return render(request, 'stats_ind.html', {'target': target, 'message':message, 'displayactions':displayactions, 'atwar':atwar,
        'alliance':alliance, 'millevel': millevel, 'displaybuilds':displaybuilds, 'homeregion':homeregion, 'region1':region1, 'region2':region2,
        'region3':region3, 'aidform':aidform, 'haswars':haswars, 'offlist':offlist, 'deflist':deflist, 'warprotection':warprotection,
        'peaceoffer':peaceoffer, 'gdpprotection':gdpprotection, 'warfuelcost':warfuelcost, 'costforgeuaid':costforgeuaid, 'indefwar':indefwar,
        'nospies':nospies, 'spyintarget':spyintarget, 'spyform':spyform, 'spyintel':spyintel, 'progress':progress, 'timeforintel':timeforintel,
        'defaultopen':defaultopen, 'hangars':hangars, 'staging':staging, 'traderessend':traderessend, 'sendtrade':sendtrade,
        'receivetrade':receivetrade, 'raidcost':raidcost, 'admin':admin, 'shiploc':shiploc, 'targetprotection':targetprotection})


def attack(request, world, target, war):
    'Calculates consequences of a war attack.'

    # variable setup
    warover = None

    worldlist = utilities.regionshiplist(world, war.region)
    totalworldpower = utilities.powerallmodifiers(world, war.region)
    baseworldpower = utilities.powerfromlist(worldlist, False)

    targetlist = utilities.regionshiplist(target, war.region)
    totaltargetpower = utilities.powerallmodifiers(target, war.region)
    basetargetpower = utilities.powerfromlist(targetlist, False)
    orgtargetlist = list(targetlist)
    orgtottargetpower = totaltargetpower

    staginglist = utilities.regionshiplist(target, 'S')
    totalstagingpower = utilities.powerallmodifiers(target, 'S')
    basestagingpower = utilities.powerfromlist(staginglist, False)

    stagingactive = hsratio = None

    lossgdp = target.gdp / 6
    lossgrowth = (target.growth/2 if target.growth > 0 else 0)
    lossbudget = target.budget / 2
    lossfuel = target.warpfuel / 2
    lossdur = target.duranium / 2
    losstrit = target.tritanium / 2
    lossadam = target.adamantium / 2
    lossfreighters = int(utilities.freighterregion(target, war.region)/6)

    wingdp = int(lossgdp*0.75)
    winbudget = int(lossbudget*D(0.75))
    winfuel = int(lossfuel*0.75)
    windur = int(lossdur*0.75)
    wintrit = int(losstrit*0.75)
    winadam = int(lossadam*0.75)
    winfreighters = int(lossfreighters*0.2)

    hangarpower = utilities.militarypower(target, 'H')
    shiplist = utilities.regionshiplist(target, 'H')
    hanglosses = utilities.war_losses(0.3*hangarpower, shiplist)
    hanglosses = utilities.hangarcalculator(world, hanglosses)

    flagworld = utilities.flagshipregion(world, war.region)
    flagtarget = utilities.flagshipregion(target, war.region)

    # involve staging fleet
    if war.region == target.region:
        stagingactive = True
        try:
            hsratio = (totaltargetpower/(totaltargetpower+totalstagingpower))
        except:
            hsratio = 1
        if sum(targetlist) == 0:
            hsratio = 0
        totaltargetpower += totalstagingpower
        basetargetpower += basestagingpower
        targetlist = [x+y for x, y in zip(targetlist, staginglist)]
        lossfreighters += int(utilities.freighterregion(target, 'S')/6)

    # automatic victory
    if 0.1*totalworldpower > basetargetpower or basetargetpower == 0:
        warover = True
        battlevictory = True

        resultdetails, htmldata = news.warresult(war.region, world, target, wingdp, 0, winbudget, winfuel,
            windur, wintrit, winadam, hanglosses, winfreighters, flagworld, flagtarget)

        newsitem = NewsItem(target=target, content=htmldata)
        newsitem.save()

    else:
        # total losses
        deflosses = utilities.war_result(totalworldpower, totaltargetpower, basetargetpower, list(targetlist), bonus=True)
        attlosses = utilities.war_result(totaltargetpower, totalworldpower, baseworldpower, list(worldlist))

        # resource salvage
        salvdur, salvtrit, salvadam = utilities.salvage([x+y for x, y in zip(deflosses, attlosses)])
        target.salvdur = F('salvdur') + salvdur
        target.salvtrit = F('salvtrit') + salvtrit
        target.salvadam = F('salvadam') + salvadam
        target.save(update_fields=['salvdur','salvtrit','salvadam'])

        # split losses between staging
        if stagingactive:
            homelosses, staginglosses = utilities.staginglosssplit(deflosses, targetlist, staginglist, hsratio)
        else:
            homelosses = deflosses
            staginglosses = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        # actually subtract ships
        utilities.warloss_byregion(target, war.region, homelosses)
        utilities.warloss_byregion(target, 'S', staginglosses)
        utilities.warloss_byregion(world, war.region, attlosses)

        # damage results for assigning victory
        damagedealt = utilities.powerfromlist(deflosses, False)
        damagesustained = utilities.powerfromlist(attlosses, False)
        battlevictory = (True if damagedealt > damagesustained else False)

        # random freighter loss
        freighterlost = random.randint(0,2)
        utilities.freighterloss(target, war.region, freighterlost)

        # flagship interaction
        flagmeet = flagworldlose = flagtargetlose = False
        if flagworld and flagtarget:
            flagmeet = True
            flagworldlose = (True if random.randint(1,50) == 1 else False)
            flagtargetlose = (True if random.randint(1,50) == 1 else False)
        elif flagworld:
            flagworldlose = (True if random.randint(1,80) == 1 else False)
        elif flagtarget:
            flagtargetlose = (True if random.randint(1,80) == 1 else False)

        if flagworldlose or flagtargetlose:
            if flagworldlose and not flagtargetlose:
                contworld = -10
                conttarget = 10
            elif flagtargetlose and not flagworldlose:
                contworld = 10
                conttarget = -10
            else:
                contworld = conttarget = 0
            utilities.contentmentchange(world, contworld)
            utilities.contentmentchange(target, conttarget)

        if flagworldlose:
            utilities.flagshipreset(world)
        if flagtargetlose:
            utilities.flagshipreset(target)

        # text results
        resultdetails, htmldata = news.battleresult(war.region, world, target, deflosses, attlosses, freighterlost,
            flagworld, flagtarget, flagmeet, flagworldlose, flagtargetlose)

        # reload worlds
        world = World.objects.get(pk=world.pk)
        target = World.objects.get(pk=target.pk)

        # testing leftovers lol
        admin = World.objects.get(pk=1)
        for i in utilities.regionshiplist(target, war.region) + utilities.regionshiplist(target, 'S'):
            if i < 0:
                NewsItem.objects.create(target=admin, content="sector: %s, attlist: %s, flagatt: %s, totatt: %s, homelist: %s, staglist: %s, totlist: %s\
                    flagdef: %s, tothome: %s, totstag: %s, totdef: %s || ratio: %s, attlosses: %s, deflosses: %s, homelosses: %s, staglosses: %s \
                    || postatt: %s, posthome: %s, poststag: %s"
                    % (repr(war.region), repr(worldlist), repr(flagworld), repr(totalworldpower), repr(orgtargetlist), repr(staginglist), repr(targetlist),
                        repr(flagtarget), repr(orgtottargetpower), repr(totalstagingpower), repr(totaltargetpower), repr(hsratio), repr(attlosses), repr(deflosses),
                        repr(homelosses), repr(staginglosses), repr(utilities.regionshiplist(world, war.region)),
                        repr(utilities.regionshiplist(target, war.region)), repr(utilities.regionshiplist(target, 'S'))))
                break

        # reload data after attack
        targetlist = utilities.regionshiplist(target, war.region)
        staginglist = utilities.regionshiplist(target, 'S')
        totalworldpower = utilities.powerallmodifiers(world, war.region)
        basetargetpower = utilities.powerfromlist(targetlist, False)
        if stagingactive:
            basetargetpower += utilities.powerfromlist(staginglist, False)

        # war end condition
        if 0.1*totalworldpower > basetargetpower or basetargetpower == 0:
            warover = True
            resultdetails, htmldata = news.finalbattleresult(war.region, world, target, deflosses, attlosses, wingdp, 0, winbudget,
                winfuel, windur, wintrit, winadam, hanglosses, freighterlost, winfreighters, flagworld, flagtarget, flagmeet,
                flagworldlose, flagtargetlose)

        NewsItem.objects.create(target=target, content=htmldata)

    if warover:

        # spoils of war
        world.gdp = F('gdp') + wingdp
        target.gdp = F('gdp') - lossgdp

        target.growth = F('growth') - lossgrowth

        world.budget = F('budget') + winbudget
        target.budget = F('budget') - lossbudget

        world.warpfuel = F('warpfuel') + winfuel
        target.warpfuel = F('warpfuel') - lossfuel

        world.duranium = F('duranium') + windur
        target.duranium = F('duranium') - lossdur

        world.tritanium = F('tritanium') + wintrit
        target.tritanium = F('tritanium') - losstrit

        world.adamantium = F('adamantium') + winadam
        target.adamantium = F('adamantium') - lossadam

        world.warpoints = F('warpoints') + 1 + target.warpoints
        target.warpoints = 0

        utilities.hangargain(world, hanglosses)
        utilities.warloss_byregion(target, 'H', hanglosses)

        utilities.freightermove(world, war.region, winfreighters)
        utilities.freighterloss(target, war.region, lossfreighters)

        h1, h2, h3, h4, h5, h6, h7, h8, h9 = hanglosses

        resourcelist = ['gdp','growth','budget','warpfuel','duranium','tritanium','adamantium','warpoints']
        world.save(update_fields=resourcelist)
        target.save(update_fields=resourcelist)

        # logs
        WarLog.objects.create(owner=world, target=target, victory=True, gdp=wingdp, growth=0, budget=winbudget,
          warpfuel=winfuel, duranium=windur, tritanium=wintrit, adamantium=winadam, fig=h1, cor=h2, lcr=h3, des=h4,
          fri=h5, hcr=h6, bcr=h7, bsh=h8, dre=h9, fre=winfreighters)
        WarLog.objects.create(owner=target, target=world, victory=False, gdp=lossgdp, growth=lossgrowth, budget=lossbudget,
            warpfuel=lossfuel, duranium=lossdur, tritanium=losstrit, adamantium=lossadam, fig=h1, cor=h2, lcr=h3, des=h4,
            fri=h5, hcr=h6, bcr=h7, bsh=h8, dre=h9, fre=lossfreighters)


        if world.worldid in War.objects.filter(defender=target).values_list('attacker', flat=True): # if you're the attacker
            # rumsoddium transfer
            if target.rumsoddium >= 1:
                world.rumsoddium = F('rumsoddium') + target.rumsoddium
                target.rumsoddium = 0
                world.save(update_fields=['rumsoddium'])
                target.save(update_fields=['rumsoddium'])
                htmldata = news.rumsoddium(world)
                NewsItem.objects.create(target=target, content=htmldata)
                resultdetails += '<p class="halfline">&nbsp;</p><span class="green">You have also taken their prized rumsoddium!</span>'
                data = GlobalData.objects.get(pk=1)
                data.rumsoddiumwars = F('rumsoddiumwars') + 1
                data.save(update_fields=['rumsoddiumwars'])
            # attribute change
            utilities.contentmentchange(target, -20)
            utilities.stabilitychange(target, -10)
            # war protection
            if not v.now() < target.brokenwarprotect:
                target.warprotection = v.now() + time.timedelta(days=5)
                target.save(update_fields=['warprotection'])

        # end of war
        war.delete()

    return render(request, 'warresult.html', {'resultdetails': resultdetails, 'battlevictory': battlevictory})


def raid(request, world, target, war):
    'Calculates consequences of a war raid.'

    # variable setup
    raidlist = utilities.regionshiplist(world, war.region)[:2] + [0, 0, 0, 0, 0, 0, 0] # only count fighters and corvettes
    totownpower = utilities.powerallmodifiers(world, war.region, raidlist, False)
    baseownpower = utilities.powerfromlist(raidlist, False)

    otherlist = utilities.regionshiplist(target, war.region)[:2] + [0, 0, 0, 0, 0, 0, 0]
    tototherpower = utilities.powerallmodifiers(target, war.region, otherlist, False)
    baseotherpower = utilities.powerfromlist(otherlist, False)

    staginglist = utilities.regionshiplist(target, 'S')[:2] + [0, 0, 0, 0, 0, 0, 0]
    totstagingpower = utilities.powerallmodifiers(target, 'S', staginglist, False)
    basestagingpower = utilities.powerfromlist(staginglist, False)

    otherfuelcost = utilities.warpfuelcost(utilities.regionshiplist(target, war.region))
    othersupply = utilities.freighterregion(target, war.region)*200

    owntraining = utilities.percenttraining(world, war.region)
    othertraining = utilities.percenttraining(target, war.region)
    stagingtraining = utilities.percenttraining(target, 'S')

    # involve staging fleet
    if war.region == target.region:
        stagingactive = True
        try:
            hsratio = (tototherpower/(tototherpower+totstagingpower))
        except:
            hsratio = 1
        tototherpower += totstagingpower
        baseotherpower += basestagingpower
        otherfuelcost += utilities.warpfuelcost(utilities.regionshiplist(target, 'S'))
        othersupply += utilities.freighterregion(target, 'S')*200
        otherlist = [x+y for x, y in zip(otherlist, staginglist)]
        if hsratio != 1:
            othertraining += stagingtraining
            othertraining /= 2

    # total losses
    deflosses = utilities.war_result(totownpower, tototherpower, baseotherpower, list(otherlist), bonus=True)
    attlosses = utilities.war_result(tototherpower, totownpower, baseownpower, list(raidlist))

    if stagingactive:
        homelosses, staginglosses = utilities.staginglosssplit(deflosses, otherlist, staginglist, hsratio)
    else:
        homelosses = deflosses
        staginglosses = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    loss = utilities.raidloss(otherfuelcost, othersupply)

    # decide winner
    upperchance = (20 if owntraining <= othertraining else 10)
    if random.randint(1, upperchance) == 1:
        supersuccess = True # victory without fighting
        success = True
    else:
        supersuccess = False

        # subtract ships
        utilities.warloss_byregion(target, war.region, homelosses)
        utilities.warloss_byregion(target, 'S', staginglosses)
        utilities.warloss_byregion(world, war.region, attlosses)

        damagedealt = utilities.powerfromlist(deflosses, False)
        damagesustained = utilities.powerfromlist(attlosses, False)

        # compare damage for winner
        if damagedealt > damagesustained or damagesustained == 0:
            success = True
            loss = utilities.raidloss(otherfuelcost, othersupply)
            utilities.freighterloss(target, war.region, loss)
        else:
            success = None
            loss = 0

    resultdetails = news.raidresult(war, world, target, deflosses, attlosses, success, supersuccess, loss)

    htmldata = news.raidnotify(war, world, target, deflosses, attlosses, success, supersuccess, loss)
    NewsItem.objects.create(target=target, content=htmldata)

    return render(request, 'raidresult.html', {'resultdetails': resultdetails, 'success': success})


def infiltrate(spy, target):
    'Results of a spy infiltration.'
    chance = random.randint(1, 100)
    if 90 + spy.infiltration >= chance:
        spy.location = target
        spy.infiltration += 1
        spy.save()
        message = 'Your agent successfully bypassed your target\'s security and got to work creating a secret network.'
    else:
        reveal, revmsg = utilities.reveal(spy)

        htmldata = news.spycaughtinfiltration(spy, reveal)
        NewsItem.objects.create(target=target, content=htmldata)

        spy.delete()

        message = 'Your agent was caught and executed by your target\'s security forces.' + revmsg
    return message


def propaganda(spy, target):
    'Results of spy propaganda.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 75 + spy.propaganda >= chance:
        spy.propaganda += 1
        spy.save(update_fields=['propaganda'])
        utilities.contentmentchange(target, -20)
        result = 'Your propaganda campaign was successful in sowing discontent among the people.'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your propaganda campaign seems to have had no effect on the populace\'s opinion of their leader.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtpropaganda(spy, reveal)
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def gunrun(spy, target):
    'Results of spy gunrunning.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 65 + spy.gunrunning >= chance:
        spy.gunrunning += 1
        spy.save(update_fields=['gunrunning'])
        utilities.rebelschange(target, 10)
        result = 'Your tech was passed on to the rebels, who successfully mount some resistance!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'The rebels make inefficient use of your tech, and there is no increase in their number.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtgunrun(spy, reveal)
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def intel(spy, target):
    'Results of spy intel.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 85 + spy.intelligence >= chance:
        spy.intelligence += 1
        spy.inteltime = v.now() + time.timedelta(hours=24)
        spy.save(update_fields=['intelligence'])
        spy.save(update_fields=['inteltime'])
        result = 'You managed to set up your electronic surveillance system successfully!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Unfortunately your network was discovered before it could collect any important data.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtintel(spy, reveal)
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabyard(spy, target):
    'Results of spy sabotaging shipyards.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 35 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])
        target.shipyards = F('shipyards') - 1
        target.save(update_fields=['shipyards'])
        htmldata = news.notifysab('yard')
        NewsItem.objects.create(target=target, content=htmldata)
        result = 'Your crack team successfully bypassed security and blew up an enemy shipyard!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was discovered by enemy security before they could destroy anything.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsab(spy, reveal, 'yard')
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabfuel(spy, target):
    'Results of spy sabotaging fuel refinery.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 45 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])
        target.warpfuelprod = F('warpfuelprod') - 10
        target.save(update_fields=['warpfuelprod'])
        htmldata = news.notifysab('fuel')
        NewsItem.objects.create(target=target, content=htmldata)
        result = 'Your team managed to sneak onto the refinery and critically damage it!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was detected by the shipyard\'s automated defense systems before they could do any damage.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsab(spy, reveal, 'fuel')
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabdur(spy, target):
    'Results of spy sabotaging duranium mine.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 45 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])
        target.duraniumprod = F('duraniumprod') - 3
        target.save(update_fields=['duraniumprod'])
        htmldata = news.notifysab('dur')
        NewsItem.objects.create(target=target, content=htmldata)
        result = 'Your crack team successfully bypassed security and destroyed an enemy duranium mine!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was discovered by enemy security before they could destroy anything.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsab(spy, reveal, 'dur')
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabtrit(spy, target):
    'Results of spy sabotaging tritanium mine.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 45 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])
        target.tritaniumprod = F('tritaniumprod') - 2
        target.save(update_fields=['tritaniumprod'])
        htmldata = news.notifysab('trit')
        NewsItem.objects.create(target=target, content=htmldata)
        result = 'Your crack team successfully bypassed security and blew up an enemy tritanium mine!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was discovered by enemy security before they could destroy anything.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsab(spy, reveal, 'trit')
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabadam(spy, target):
    'Results of spy sabotaging adamantium mine.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 45 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])
        target.adamantiumprod = F('adamantiumprod') - 1
        target.save(update_fields=['adamantiumprod'])
        htmldata = news.notifysab('adam')
        NewsItem.objects.create(target=target, content=htmldata)
        result = 'Your crack team successfully bypassed security and blew up an enemy adamantium mine!'
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was discovered by enemy security before they could destroy anything.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsab(spy, reveal, 'adam')
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message


def sabhangars(spy, target):
    'Results of spy sabotaging hangar.'
    caughtmsg = revmsg = ''
    chance = random.randint(1, 100)
    if 45 + spy.sabotage >= chance:
        spy.sabotage += 2
        spy.save(update_fields=['sabotage'])

        targetpower = utilities.militarypower(target, 'H')
        shiplist = utilities.regionshiplist(target, 'H')
        deflosses = utilities.war_losses(0.1*targetpower, shiplist)
        utilities.warloss_byregion(target, 'H', deflosses)

        htmldata = news.notifysabhangars(deflosses)
        NewsItem.objects.create(target=target, content=htmldata)

        hangarlosses = news.losses(deflosses)

        result = "You successfully managed to sabotage the enemy's orbital hangars, and destroyed%s as a result!" % hangarlosses
    else:
        caught, caughtmsg = utilities.caught(spy)
        result = 'Your covert team was discovered by enemy security before they could destroy anything.'
        if caught:
            reveal, revmsg = utilities.reveal(spy)

            htmldata = news.spycaughtsabhangars(spy, reveal)
            NewsItem.objects.create(target=target, content=htmldata)

            spy.delete()

    message = result + caughtmsg + revmsg
    return message
