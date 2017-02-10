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
    logged_in = request.user.is_authenticated()
    if logged_in:
        worlds = World.objects.select_related('preferences', 'alliance').filter(Q(pk=userid)|Q(user=request.user))
        #1 query instead of 4
        target = worlds.get(pk=userid)
        world = worlds.get(user=request.user)
        displayactions = True
    else:
        target = World.objects.select_related('preferences', 'alliance').get(pk=userid)
        world = World() #anon user
    if target.pk == world.pk:
        return redirect('main') # redirect to your own page


    # variable setup
    message = ""
    atwar = haswars = offlist = deflist = admin = None
    warprotection = gdpprotection = targetprotection = None
    peaceoffer = warfuelcost = raidcost = None
    costforgeuaid = indefwar = None
    nospies = spyintarget = spyform = spyintel = timeforintel = None
    aidform = traderessend = sendtrade = receivetrade = None
    defaultopen = 'domestic,economic,diplomacy,military'
    lastseen = str(v.now() - target.lastloggedintime).split(',')[0]
    alliance = target.alliance

    # military levels setup
    millevel = world.techlevel
    displayactions = (True if logged_in else False)
    try:
        if world.preferences.vacation:
            raise Exception # not allowed to take actions when you're on vacation
    except:
        pass
    else:
        defaultopen = world.statsopenprefs

        # war status
        if world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True):
            atwar = True
            war = War.objects.get(attacker=world, defender=target)
            if war.peaceofferbyatk is not None:
                peaceoffer = True
        elif world.pk in War.objects.filter(attacker=target).values_list('defender', flat=True):
            atwar = True
            war = War.objects.get(attacker=target, defender=world)
            if war.peaceofferbydef is not None:
                peaceoffer = True

        if abs(world.econsystem - target.econsystem) == 2:
            costforgeuaid = True

        if world.wardefender.count() > 0:
            indefwar = True

        # convenience admin links
        if world.pk == 1:
            admin = True

        if request.method == 'POST' and logged_in:
            form = request.POST

            if "sendcomm" in form:
                if SentComm.objects.filter(sender=world, 
                    datetime__gte=v.now()-time.timedelta(seconds=v.delay)).count() > v.commlimit:
                    message = "Stop spamming"
                else:
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
                ownpower = utilities.totalpower(world)
                targetpower = utilities.totalpower(target)
                if target.preferences.vacation:
                    message = 'This world is in vacation mode. You cannot declare war on it.'
                elif ownpower == 0:
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

                    War.objects.create(attacker=world, defender=target, reason=warreason)

                    htmldata = news.wardec(world,warreason)
                    NewsItem.objects.create(target=target, content=htmldata)

                    world.declaredwars.add(target)
                    action = {'warsperturn': {'action': 'add', 'amount': 1}}
                    utilities.atomic_world(world.pk, action)
                    message = 'You have declared WAR!' + endprotect + aboveprotect

            if "attack" in form and atwar is None:
                message = 'You are not at war with this world!'
            elif "attack" in form:
                form = attackform(world, request.POST['attack'], request.POST)
                if form.is_valid():
                    fuelcost = 0
                    enemybp = 0
                    sector = form.cleaned_data['fleets'][0].sector
                    ineligiblefleets = []
                    for fleeet in form.cleaned_data['fleets']:
                        fuelcost += fleeet.fuelcost()
                        if fleeet.attacked:
                            ineligiblefleets.append(['', fleeet.name])
                    for f in fleet.objects.filter(controller=target, sector=sector):
                        enemybp += f.power()
                    if world.warpfuel < fuelcost:
                        message = 'You do not have enough warpfuel to support this attack!'
                    elif len(ineligiblefleets) > 0:
                        message = utilities.resource_text(ineligiblefleets).replace('  ', ' ')
                        message += 'need to reorganise and rearm until they can attack again!' 
                    elif enemybp == 0 and sector != target.sector:
                        message = "Can't attack enemy fleets in %s, there are none!" % sector
                    else:
                        if world in War.objects.filter(defender=target) and v.now() < world.warprotection:
                            world.warprotection = v.now()
                        actions = {'warpfuel': {'action': 'subtract', 'amount': fuelcost}}
                        utilities.atomic_world(world.pk, actions)
                            #extract sector from fleet location
                        return attack(request, world, target, form.cleaned_data['fleets'], war)

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
                elif world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True) and war.timetonextattack > v.now():
                    timedifference = war.timetonextattack - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                elif world.pk in War.objects.filter(attacker=target).values_list('defender', flat=True) and war.timetonextdefense > v.now():
                    timedifference = war.timetonextdefense - v.now()
                    hours, minutes, seconds = utilities.timedeltadivide(timedifference)
                    message = 'You cannot launch another attack so soon! Your fleet still needs %s:%s:%s to \
                        regroup before it can launch another attack.' % (hours, minutes, seconds)
                else:
                    if world in War.objects.filter(defender=target) and v.now() < world.warprotection:
                        world.warprotection = v.now()
                        world.save(update_fields=['warprotection'])

                    if world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        war.timetonextattack = v.now() + time.timedelta(hours=8)
                    elif world.pk in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        war.timetonextdefense = v.now() + time.timedelta(hours=8)
                    war.save()

                    utilities.wearinesschange(world, war.region, -5)

                    world.warpfuel = F('warpfuel') - raidcost
                    world.save(update_fields=['warpfuel'])
                    world = World.objects.get(pk=world.pk)

                    return raid(request, world, target, war)

            if 'peace' in form:
                if atwar is None:
                    message = 'You are not at war with this world!'
                else:
                    if form['peace'] == 'offerpeace':
                        htmldata = news.offerpeace(world, target)
                        newsitem = ActionNewsItem.objects.create(target=target, content=htmldata, actiontype=1)
                    else:
                        htmldata = news.peacerevoke(world)
                        NewsItem.objects.create(target=target, content=htmldata)

                    if world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True):
                        if form['peace'] == 'offerpeace':
                            war.peaceofferbyatk = newsitem
                        else:
                            try:
                                war.peaceofferbyatk.delete()
                            except: pass
                    elif world.pk in War.objects.filter(attacker=target).values_list('defender', flat=True):
                        if form['peace'] == 'offerpeace':
                            war.peaceofferbydef = newsitem
                        else:
                            try:
                                war.peaceofferbydef.delete()
                            except: pass
                    war.save()
                    if form['peace'] == 'offerpeace':
                        message = 'An offer of peace has been sent, which your enemy will have to accept.'
                    else:
                        peaceoffer = None
                        message = 'You have revoked your peace offer.'

            if 'directaid' in form:
                form = Aidform(world, request.POST)
                if world.gdp < 250:
                    message = 'Your world\'s economy is too weak to support your humanitarian efforts!'
                elif form.is_valid():
                    actions = {}
                    tgtactions = {}
                    resources = []
                    required_capacity = 0
                    data = form.cleaned_data
                    reference = []
                    reference += v.resources
                    geu = False
                    for resource in reference:
                        if data.has_key(resource) and resource == 'budget': #instant transfer
                            if data[resource] == 0:
                                continue
                            action = {'budget': {'action': 'add', 'amount': data[resource]}}
                            utilities.atomic_world(world.pk, action, target.pk)
                            htmldata = news.directaidcompletion(world, [['GEU', data[resource]]])
                            NewsItem.objects.create(target=target, content=htmldata)
                            #logs
                            tgtlog = ResourceLog.objects.create(owner=target, target=world)
                            Logresource.objects.create(resource="GEU", amount=data[resource], log=tgtlog)
                            message = "%s has recieved %s %s!" % (target.name, data[resource], 'GEU')
                        else:
                            if data.has_key(resource) and data[resource] > 0:
                                resources.append([resource, data[resource]])
                                required_capacity += v.freighter_capacity[resource] * data[resource]
                                actions.update({resource: {'action': 'subtract', 'amount': data[resource]}})
                                tgtactions.update({resource: {'action': 'add', 'amount': data[resource]}})

                    freighters = world.freighters - world.freightersinuse
                    required_freighters = (required_capacity / v.freighter_capacity['total'])+ 1
                    if len(resources) == 0: #pure budget aid
                        pass
                    elif freighters >= required_freighters:
                        #gots enough freighters
                        delay = (1 if world.sector == target.sector else 2)
                        outcometime = datetime=v.now() + time.timedelta(hours=delay)
                        actions.update({
                        'freightersinuse': {'action': 'add', 'amount': required_freighters},                              
                        })
                        utilities.atomic_world(world.pk, actions)
                        taskdetails = taskdata.directaidarrival(world, resources)
                        task = Task.objects.create(target=target, 
                            content=taskdetails, datetime=outcometime)
                        newtask.directaid.apply_async(args=(world.pk, target.pk, 
                            task.pk, resources, freighters), eta=outcometime)
                        if data['budget'] > 0:
                            resources = [['GEU', data['budget']]] + resources
                        #create logs!
                        log = ResourceLog.objects.create(owner=world, target=target, sent=True)
                        for resource in resources:
                            Logresource.objects.create(resource=resource[0], amount=resource[1], log=log)
                        hour = ('hours' if delay == 2 else 'hour')
                        if len(message):
                            message = message[:-1] + " and will recieve  %s in %s %s!" % (
                            utilities.resource_text(resources), delay, hour)
                        else:
                            message = "%s will recieve %s in %s %s!" % (
                            target.name, utilities.resource_text(resources), delay, hour)
                    else: #not enough freighters                                    
                        message = "We do not have enough freighters, we have %s and need %s" % (freighters, required_freighters)
            
            if 'shipaid' in form:
                form = Shipaidform(world, form)
                if form.is_valid():
                    data = form.cleaned_data
                    ship = data['ship_choice']
                    amount = data['amount']
                    delay = (4 if target.sector == world.sector else 8)
                    outcometime = datetime=v.now() + time.timedelta(minutes=1)
                    if data['amount'] > data['fleet_choice'].__dict__[data['ship_choice']]:
                        message = "%s doesn't have that many %s!" % (data['fleet_choice'].name, ship)
                    else: #is all good
                        action = {'subtractships': {data['ship_choice']: amount}}
                        utilities.atomic_fleet(data['fleet_choice'].pk, action)
                        log = ResourceLog.objects.create(owner=world, target=target, sent=True)
                        shipname = (ship.replace('_', ' ') if amount > 1 else ship[:-1].replace('_', ' ')) #to plural or not plural
                        Logresource.objects.create(resource=shipname, amount=amount, log=log)
                        #more stuff
                        ref = fleet()
                        ref.__dict__[ship] = amount
                        training = data['fleet_choice'].maxtraining() * data['fleet_choice'].ratio() 
                        taskdetails = taskdata.shipaidarrival(world, shipname, amount)
                        task = Task.objects.create(target=target, 
                            content=taskdetails, datetime=outcometime)
                        newtask.shipaid.apply_async(args=(world.pk, target.pk, 
                            task.pk, ship, amount, training), eta=outcometime)
                        message = "%s %s is en route to %s from %s" % (
                            amount, shipname, target.name, data['fleet_choice'].name)

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
                        if target.preferences.vacation:
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
                        actions = {'budget': {'action': 'subtract', 'amount': 250}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 200}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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
                        actions = {'budget': {'action': 'subtract', 'amount': 2000}}
                        utilities.atomic_world(world.pk, actions)
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

        if world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True):
            atwar = True
            war = War.objects.get(attacker=world, defender=target)
            if war.peaceofferbyatk is not None:
                peaceoffer = True
        elif world.pk in War.objects.filter(attacker=target).values_list('defender', flat=True):
            atwar = True
            war = War.objects.get(attacker=target, defender=world)
            if war.peaceofferbydef is not None:
                peaceoffer = True

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

        if Spy.objects.filter(owner=world).filter(location=target).count() == 1:
            spyintarget = Spy.objects.filter(owner=world, location=target)[0]
            if spyintarget.inteltime > v.now():
                spyintel = True
                timediff = spyintarget.inteltime - v.now()
                hours, minutes, seconds = utilities.timedeltadivide(timediff)
                timeforintel = 'You have %s:%s:%s of intel remaining.' % (hours, minutes, seconds)
    #if the two worlds are at war
    #calculate what fleets can attack where and what buttons to render
    attackforms = []
    if atwar:  
        worldfleets = world.controlled_fleets.all().exclude(sector='warping').exclude(sector='hangar')
        targetfleets = target.controlled_fleets.all().exclude(sector='warping').exclude(sector='hangar')
        sectors = {'amyntas': 0, 'bion': 0, 'cleon': 0, 'draco': 0}
        for unit in worldfleets:
            sectors[unit.sector] = 1
            if unit.sector == target.sector:
                sectors[unit.sector] = 2
        for unit in targetfleets:
            sectors[unit.sector] += 1
        for sector in v.sectors: #organised list so it shows amyntas -> draco
            if sectors[sector] >= 2: #both worlds has fleets in given sector
                attackforms.append({'form': attackform(world, sector), 'sector': sector})
        if len(attackforms) == 0:
            attackforms = False #so we can display error message
    milinfo = utilities.mildisplaylist(target, main=False)
    mildisplay = display.fleet_display(milinfo[0], milinfo[1], main=False)
    target.refresh_from_db()
    if target.warattacker.count() > 0 or target.wardefender.count() > 0:
        haswars = True
        offlist = [wars.defender for wars in target.warattacker.all()]
        deflist = [wars.attacker for wars in target.wardefender.all()]
    initdata = {}
    for resource in v.resources:
        if world.__dict__[resource] > 0:
            initdata.update({resource: 0})
    

    return render(request, 'stats_ind.html', {'target': target, 'displayactions': displayactions, 'message':message, 'atwar':atwar,
        'alliance':alliance, 'millevel': millevel, 'aidfleet': aidfleetform(world), 'aidform':Aidform(world, initial=initdata), 'haswars':haswars, 'offlist':offlist, 'deflist':deflist, 'warprotection':warprotection,
        'peaceoffer':peaceoffer, 'gdpprotection':gdpprotection, 'warfuelcost':warfuelcost, 'costforgeuaid':costforgeuaid, 'indefwar':indefwar,
        'nospies':nospies, 'spyintarget':spyintarget, 'mildisplay': mildisplay, 'spyform':spyform, 'spyintel':spyintel, 'timeforintel':timeforintel,
        'defaultopen':defaultopen, 'lastonline': display.lastonline(target), 'attackforms': attackforms, 'shipaid': Shipaidform(world),
        'receivetrade':receivetrade, 'lastseen': lastseen, 'raidcost':raidcost, 'targetprotection':targetprotection})



def battle(attacker, defender):
    pass



def attack(request, world, target, fleets, war):
    'Calculates consequences of a war attack.'
    # variable setup
    actions = {}
    targetactions = {}
    sector = fleets[0].sector
    flagworld = flagtarget = False
    defensefleets = target.controlled_fleets.all().filter(sector=sector)
    OOS  = (True if sector != target.sector else False) #out of sector combat gets no def bonus
    warover = False
    surrender = False
    #attacker setup
    baseworldpower = totalworldpower = 0
    for ships in fleets:
        totalworldpower += ships.powermodifiers()
        baseworldpower += ships.basepower()
        if ships.flagship:
            flagworld = True
    #defender setup
    basetargetpower = totaltargetpower = 0
    for ships in defensefleets:
        print ships.basepower(), ships.powermodifiers()
        totaltargetpower += ships.powermodifiers()
        basetargetpower += ships.basepower()
        if ships.flagship:
            flagtarget = True

    # automatic victory
    if (0.1*totalworldpower > basetargetpower or basetargetpower == 0) and OOS == False:
        #no automatic victory for OOS combat
        warover = True
        battlevictory = True
        surrender = True
    else:
        # total damage per world
        if OOS:
            attackdamage = utilities.war_result(totalworldpower, totaltargetpower, basetargetpower)
        else:
            attackdamage = utilities.war_result(totalworldpower, totaltargetpower, basetargetpower, bonus=True)
        defensedamage = utilities.war_result(totaltargetpower, totalworldpower, baseworldpower)
        #now we determine how much damage each fleet sustained
        allfleets = {}
        for balls in fleets:
            ratio = float(balls.basepower()) / float(baseworldpower)
            sustained = defensedamage * ratio
            allfleets.update({balls: sustained})
        for balls in defensefleets:
            ratio = float(balls.basepower()) / float(basetargetpower)
            sustained = attackdamage * ratio
            allfleets.update({balls: sustained})
        #determine shiplosses
        allfleetlosses = {}
        worldloss = fleet()
        targetloss = fleet()
        p = []
        for fleetobj, damage in allfleets.iteritems():
            allfleetlosses.update({fleetobj.pk: utilities.war_losses(damage, fleetobj)})
            p.append(allfleetlosses[fleetobj.pk].heidilist())
            if fleetobj.controller == world:
                worldloss.merge(allfleetlosses[fleetobj.pk])
            else:
                targetloss.merge(allfleetlosses[fleetobj.pk])
        #nukiepants the fleets
        totaldeath = fleet()
        for fleetpk, losses in allfleetlosses.iteritems():
            utilities.atomic_fleet(fleetpk, {'loss': losses})
            totaldeath.merge(losses)

        # resource salvage
        salvdur, salvtrit, salvadam = utilities.salvage(totaldeath)
        if OOS:
            Salvage.objects.create(sector=sector, duranium=salvdur, tritanium=salvtrit, adamantium=salvadam)
        else:
            targetactions.update({
                'salvdur': {'action': 'add', 'amount': salvdur},
                'salvtrit': {'action': 'add', 'amount': salvtrit},
                'salvadam': {'action': 'add', 'amount': salvadam},
                })

        # damage results for assigning victory
        battlevictory = (True if attackdamage > defensedamage else False)

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

        #doublecheck outcome
        if not flagtargetlose:
            for ships in defensefleets:
                if ships.flagship:
                    ships.refresh_from_db()
                    if ships == fleet():
                        flagtargetlose = True
        #necessary because reasons
        #nah for realios
        #flagships is rngesus and an obliterated fleet with intact flagship is no
        #so if fleet got decimated flagship is kill as well

        if flagworldlose or flagtargetlose:
            if flagworldlose and not flagtargetlose:
                actions.update({'contentment': {'action': 'add', 'amount': utilities.attrchange(world.contentment, -10)}})
                targetactions.update({'contentment': {'action': 'add', 'amount': utilities.attrchange(target.contentment, 10)}})
            elif flagtargetlose and not flagworldlose:
                actions.update({'contentment': {'action': 'add', 'amount': utilities.attrchange(world.contentment, 10)}})
                targetactions.update({'contentment': {'action': 'add', 'amount': utilities.attrchange(target.contentment, -10)}})
            utilities.atomic_world(target.pk, targetactions)
            utilities.atomic_world(world.pk, actions)
            targetactions = {}
            actions = {}

        if flagworldlose:
            for f in fleets:
                if f.flagship:
                    utilities.atomic_fleet(f.pk, {'set': {'flagship': False}})
        if flagtargetlose:
            for f in defensefleets:
                if f.flagship:
                    utilities.atomic_fleet(f.pk, {'set': {'flagship': False}})

        # reload worlds
        world.refresh_from_db()
        target.refresh_from_db()

        # reload data after attack
        defensefleets = target.controlled_fleets.all().filter(sector=sector)
        baseworldpower = totalworldpower = 0
        for ships in fleets:
            ships.refresh_from_db()
            totalworldpower += ships.powermodifiers()
            baseworldpower += ships.basepower()
        #defender setup
        basetargetpower = totaltargetpower = 0
        for ships in defensefleets:
            totaltargetpower += ships.powermodifiers()
            basetargetpower += ships.basepower()
        #setting flagship data for easy manipulation
        #or at least easier than passing every variable like heidi did
        flag = {'world': flagworld, 'target': flagtarget, 'worldloss': flagworldlose, 'targetloss': flagtargetlose,
            'worldname': world.flagshipname, 'targetname': target.flagshipname, 'meet': flagmeet}
        # war end condition
        if OOS and basetargetpower == 0:
            print "Triggered"
            #OOS war end calculations and sheeit
            surplusfreighters = 0
            for ships in defensefleets:
                surplusfreighters += ships.freighters
                #attacker takes remaining freighters for himself
                utilities.atomic_fleet(ships.pk, {'set': {'freighters': 0}}) 
                #freighters are distributed evenly between attacking fleets
                #but preferentially given to those who needs them
            for ships in fleets:
                if ships.enoughfuel()[1] == 'freighters': #fleet needs freighters to function
                    needed = (ships.fuelcost() * v.freighter_capacity['warpfuel'] / \
                    v.freighter_capacity['total']) + 1
                    if surplusfreighters >= needed:
                        surplusfreighters -= needed
                        atomic_fleet(ships.pk, {'add': {'freighters': needed}})
                    else:
                        surplusfreighters = 0
                        atomic_fleet(ships.pk, {'add': {'freighters': surplusfreighters}})
                        break
            stolenfreighters = surplusfreighters

            assignment = [0] * len(fleets)
            if surplusfreighters > len(fleets):
                for n in assignment:
                    n += 1
                    surplusfreighters -= 1
            while surplusfreighters > 0:
                assignment[random.randint(0, len(assignment)-1)] += 1
                surplusfreighters -= 1
            for ships, freighters in zip(fleets, assignment):
                utilities.atomic_fleet(ships.pk, {'add': {'freighters': freighters}})

            resultdetails, htmldata = news.OOSfinalbattleresult(sector, world, target, worldloss, 
                targetloss, stolenfreighters, fleets, defensefleets, flag)

        elif (0.1*totalworldpower > basetargetpower or basetargetpower == 0) and not OOS:
            #home sector victory battle
            warover = True
        else:
            #regular combat result
            resultdetails, htmldata = news.battleresult(sector, world, target, worldloss, 
                targetloss, fleets, defensefleets, flag)

            NewsItem.objects.create(target=target, content=htmldata)

    if warover:
        losses = { #maximum losses
        'warpfuel': (target.warpfuel / 2 if target.warpfuel > 0 else 0),
        'duranium': (target.duranium / 2 if target.duranium > 0 else 0),
        'tritanium': (target.tritanium / 2 if target.tritanium > 0 else 0),
        'adamantium': (target.adamantium / 2 if target.adamantium > 0 else 0),
        }
        capacity = 0
        for ships in fleets:
            capacity += ships.__dict__['freighters'] * v.freighter_capacity['total']
        preferred = world.preferences.winresource
        actions = {
        'warpoints': {'action': 'add', 'amount': target.warpoints+1},
        'budget': {'action': 'add', 'amount': (target.budget / 2 if target.budget > 0 else 0)},
        'gdp': {'action': 'add', 'amount': (target.gdp / 6 if target.gdp > 0 else 0)},
        'growth': {'action': 'add', 'amount': (target.growth/2 if target.growth > 0 else 0)},
        }
        if capacity > losses[preferred] * v.freighter_capacity[preferred]:
            actions.update({preferred: {'action': 'add', 'amount': losses[preferred] * v.freighter_capacity[preferred]}})
            capacity -= losses[preferred] * v.freighter_capacity[preferred]
        else:
            actions.update({preferred: {'action': 'add', 'amount': 0}})
            while capacity > v.freighter_capacity[preferred]:
                actions[preferred]['amount'] += 1
                capacity -= v.freighter_capacity[preferred]

        losses.pop(preferred)
        while capacity > 0: #distribute war loot lol
            nogo = 0
            for item in losses: #even distribution for the non-preferred resources
                if losses[item] == 0:
                    nogo += 1
                    continue
                if capacity >= v.freighter_capacity[item]:
                    if actions.has_key(item):
                        actions[item]['amount'] += 1
                    else:
                        actions.update({item: {'action': 'add', 'amount': 1}})
                    capacity -= v.freighter_capacity[item]
                    losses[item] -= 1
                else:
                    nogo += 1
            if sum(losses.values()) == 0 or nogo == len(losses):
                break

        resources = ['gdp', 'growth'] + v.resources #for proper display
        #because dicts aren't ordered
        for key in resources[:]: #workaround for python being lazy
            if not actions.has_key(key):
                resources.remove(key)
                continue 
            targetactions.update({key: {'action': 'subtract', 'amount': actions[key]['amount']}})
        targetactions.update({'warpoints': {'action': 'set', 'amount': 0}})
        # logs
        winlog = Warlog(owner=world, target=target, victory=True)
        winlog.set(actions, resources)
        winlog.save()
        loserlog = Warlog(owner=target, target=world, victory=False)
        loserlog.set(actions, resources, reverse=True)
        winlog.save()
        if surrender:
            resultdetails, htmldata = news.warresult(sector, world, target, actions, 
                ' no ships at all', 0, fleets, defensefleets)
        else:
            resultdetails, htmldata = news.finalbattleresult(sector, world, target, actions, 
                resources, ' no ships at all', worldloss, targetloss, fleets, defensefleets)
        newsitem = NewsItem(target=target, content=htmldata)
        newsitem.save()


        if world.pk in War.objects.filter(defender=target).values_list('attacker', flat=True): # if you're the attacker
            # rumsoddium transfer
            if target.rumsoddium >= 1:
                actions.update({'rumsoddium': {'action': 'add', 'amount': target.rumsoddium}})
                targetactions.update({'rumsoddium': {'action': 'set', 'amount': 0}})
                htmldata = news.rumsoddium(world)
                NewsItem.objects.create(target=target, content=htmldata)
                resultdetails += '<p class="halfline">&nbsp;</p><span class="green">You have also taken their prized rumsoddium!</span>'
                data = GlobalData.objects.get(pk=1)
                data.rumsoddiumwars = F('rumsoddiumwars') + 1
                data.save(update_fields=['rumsoddiumwars'])
            # attribute change
            targetactions.update({
                'contentment': {'action': 'add', 'amount': utilities.attrchange(target.contentment, -20)},
                'stability': {'action': 'add', 'amount': utilities.attrchange(target.stability, -10)}
                })
            # war protection
            if not v.now() < target.brokenwarprotect:
                targetactions.update({'warprotection': {'action': 'set', 'amount': v.now() + time.timedelta(days=5)}})
        # end of war
        war.delete()
        utilities.atomic_world(world.pk, actions)
        utilities.atomic_world(target.pk, targetactions)

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
        cont = utilities.attrchange(target.contentment, -20)
        utilities.atomic_world(target.pk, {'contentment': {'action': 'add', 'amount': cont}})
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
        rebels = utilities.attrchange(target.rebels, 10, zero=True)
        utilities.atomic_world(target.pk, {'rebels': {'action': 'add', 'amount': rebels}})
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
        spy.save(update_fields=['intelligence', 'inteltime'])
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
        actions = {'shipyards': {'action': 'subtract', 'amount': 1}}
        if target.productionpoints > target.shipyards:
            reduction = target.productionpoints / target.shipyards
            actions.update({'productionpoints': {'action': 'subtract', 'amount': reduction}})
        utilities.atomic_world(target.pk, actions)
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
        utilities.atomic_world(target.pk, {'warpfuelprod': {'action': 'subtract', 'amount': v.production['warpfuelprod']}})
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
        utilities.atomic_world(target.pk, {'duraniumprod': {'action': 'subtract', 'amount': v.production['duraniumprod']}})
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
        utilities.atomic_world(target.pk, {'tritaniumprod': {'action': 'subtract', 'amount': v.production['tritaniumprod']}})
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
        utilities.atomic_world(target.pk, {'adamantiumprod': {'action': 'subtract', 'amount': v.production['adamantiumprod']}})
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
