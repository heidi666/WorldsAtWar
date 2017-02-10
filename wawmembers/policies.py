# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import F
from django.db.models import Min
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import random, decimal
import datetime as time

# WaW Imports
from wawmembers.models import *
from wawmembers.forms import *
from wawmembers.decorators import world_required, noaction_required
import wawmembers.tasks as newtask
import wawmembers.display as display
import wawmembers.outcomes_policies as outcomes
import wawmembers.newsgenerator as news
import wawmembers.taskgenerator as taskdata
import wawmembers.utilities as utilities
import wawmembers.variables as v

'''
Display and actions for policy pages: economic, domestic, diplomatic and fleet.
'''


D = decimal.Decimal


@login_required            ## ECONOMIC
@world_required
@noaction_required
def policies_econ(request):

    # variable setup
    world = request.user.world
    result = rumsodmsg = None
    salvagecost = 2 * (world.salvdur + world.salvtrit + world.salvadam)
    salvagecost = (100 if salvagecost < 100 else salvagecost)
    shownoob = (True if world.gdp <= 115 else None)
    showtrit = (True if world.millevel >= v.millevel('lcr') else False)
    showadam = (True if world.millevel >= v.millevel('hcr') else False)
    rescosts = {
    'warpfuelprod': (v.production['warpfuelprod']['cost'] if world.sector != 'cleon' else v.production['warpfuelprod']['cost'] * v.bonuses['cleon']),
    'duraniumprod': (v.production['duraniumprod']['cost'] if world.sector != 'cleon' else v.production['duraniumprod']['cost'] * v.bonuses['cleon']),
    'tritaniumprod': (v.production['tritaniumprod']['cost'] if world.sector != 'cleon' else v.production['tritaniumprod']['cost'] * v.bonuses['cleon']),
    'adamantiumprod': (v.production['adamantiumprod']['cost'] if world.sector != 'cleon' else v.production['adamantiumprod']['cost'] * v.bonuses['cleon']),
    }

    if request.method == 'POST':
        form = request.POST
        actions = False
        if "noobgrowthpolicy" in form:
            if world.budget < 70:
                result = outcomes.nomoney()
            elif not shownoob:
                result = outcomes.noobgrowth('TooRich')
            elif world.growth >= 100:
                result = outcomes.toomuchgrowth()
            else:
                actions = {
                'growth': {'action': 'add', 'amount': 2},
                'budget': {'action': 'subtract', 'amount': 70},
                }
                result = outcomes.noobgrowth('Success')

        if "forcedlabour" in form:
            if world.polsystem > -60:
                result = outcomes.forcedlabour('NotDictatorship')
            elif world.stability < -80:
                result = outcomes.forcedlabour('StabilityTooLow')
            else:
                outcome = random.randint(1, 100)
                content = utilities.attrchange(world.contentment, -10)
                stability = utilities.attrchange(world.stability, -5)
                actions = {
                'contentment': {'action': 'add', 'amount': content},
                'stability': {'action': 'add', 'amount': stability},
                }
                if 15 < outcome <= 100:
                    actions.update({'growth': {'action': 'add', 'amount': 5}})
                if 1 <= outcome <= 5:
                    actions.update({'rebels': {'action': 'add', 'amount': 10}})
                result = outcomes.forcedlabour(outcome)

        if "nationalise" in form:
            if world.econsystem == -1:
                result = outcomes.nationalise('NotFreeOrMixed')
            elif world.econchanged:
                result = outcomes.nationalise('Already')
            else:
                stab = utilities.attrchange(world.stability, -20)
                actions = {
                'econchanged': {'action': 'set', 'amount': True},
                'stability': {'action': 'add', 'amount': stab},
                'econsystem': {'action': 'subtract', 'amount': 1},
                }
                result = outcomes.nationalise('Success')

        if "privatise" in form:
            if world.econsystem == 1:
                result = outcomes.privatise('NotCPorMixed')
            elif world.econchanged:
                result = outcomes.nationalise('Already')
            else:
                stab = utilities.attrchange(world.stability, -20)
                actions = {
                'econchanged': {'action': 'set', 'amount': True},
                'stability': {'action': 'add', 'amount': stab},
                'econsystem': {'action': 'subtract', 'amount': 1},
                }
                result = outcomes.privatise('Success')

        if 'build' in form:
            if form['build'] in v.production:
                build = form['build']
                if build == 'warpfuelprod' or build == 'duraniumprod':
                    canbuild = True
                elif build == 'tritaniumprod' and showtrit:
                    canbuild = True
                elif build == 'adamantiumprod' and showadam:
                    canbuild = True
                else:
                    canbuild = False
                if canbuild:
                    if world.budget < v.production[build]['cost']:
                        result = outcomes.nomoney()
                    else:
                        actions = {'budget': {'action': 'subtract', 'amount': D(rescosts[build])}}
                        modifier = v.production[build]['chance']
                        if modifier > 10:
                            modifier = (modifier-30 if world.sector == "cleon" else modifier)
                        else:
                            modifier = (modifier-3 if world.sector == "cleon" else modifier)

                        if modifier < random.randint(1, 100) <= 100:
                            actions.update({build: {'action': 'add', 'amount': v.production[build]['production']}})
                            result = outcomes.prospecting[build]('Success')
                        else:
                            result = outcomes.prospecting[build]('Failure')
                result = "You've been a naughty boy" 

        if 'close' in form:
            form = mineshutdownform(world, request.POST)
            if form.is_valid():
                prodtype = form.cleaned_data['mine']
                actions= {
                    prodtype: {'action': 'subtract', 'amount': v.production[prodtype]['production']},
                    'inactive_%s' % prodtype: {'action': 'add', 'amount': 1}
                    }
                result = outcomes.shutdown(prodtype[:-4])
            else:
                result = outcomes.nomines(prodtype[:-4])

        if 'reopen' in form:
            form = reopenmineform(world, request.POST)
            if form.is_valid():
                prodtype = form.cleaned_data['mine']
                actions = {
                    'inactive_%s' % prodtype: {'action': 'subtract', 'amount': 1},
                    'resuming_%s' % prodtype: {'action': 'add', 'amount': 1},
                    }
                result = outcomes.reopen(prodtype[:-4])
            else:
                result = "Inspect element is naughty (and won't work)"


        if "salvagemission" in form:
            if world.budget < salvagecost:
                result = outcomes.nomoney()
            elif world.turnsalvaged:
                result = outcomes.salvagemission('AlreadySalvaged')
            elif world.salvdur + world.salvtrit + world.salvadam == 0:
                result = outcomes.salvagemission('NoSalvage')
            else:
                salvmin = (70 if world.sector == 'C' else 60)
                salvmax = (80 if world.sector == 'C' else 70)
                dur = int(round(world.salvdur * random.randint(salvmin, salvmax) / 100.0))
                trit = int(round(world.salvtrit * random.randint(salvmin, salvmax) / 100.0))
                adam = int(round(world.salvadam * random.randint(salvmin, salvmax) / 100.0))
                actions = {
                'budget': {'action': 'subtract', 'amount': D(salvagecost)},
                'salvdur': {'action': 'subtract', 'amount': dur},
                'duranium': {'action': 'add', 'amount': dur},
                'salvtrit': {'action': 'subtract', 'amount': trit},
                'tritanium': {'action': 'add', 'amount': trit},
                'salvadam': {'action': 'subtract', 'amount': adam},
                'adamantium': {'action': 'add', 'amount': adam},
                'turnsalvaged': {'action': 'set', 'amount': True},
                }
                result = outcomes.salvagemission([dur,trit,adam])

        if "rumsodecon" in form: #make more powerful, is way useless
            if world.rumsoddium != 4:
                result = 'You do not have enough rumsoddium for the ritual!'
            else:
                actions = {
                'gdp': {'action': 'add', 'amount': world.gdp},
                'budget': {'action': 'add', 'amount': D(world.gdp*6)},
                'warpfuel': {'action': 'add', 'amount': world.warpfuel},
                'duranium': {'action': 'add', 'amount': world.duranium},
                'tritanium': {'action': 'add', 'amount': world.tritanium},
                'adamantium': {'action': 'add', 'amount': world.adamantium},
                'rumsoddium': {'action': 'set', 'amount': 0}
                }
                rumsodmsg = v.rumsodeconomy
                utilities.rumsoddiumhandout()
        if actions: #easier than putting the line in every policy conditional
            utilities.atomic_world(world.pk, actions)
            world.refresh_from_db()

    salvagecost = 2 * (world.salvdur + world.salvtrit + world.salvadam)
    salvagecost = (100 if salvagecost < 100 else salvagecost)
    salvagetext = news.salvagetext(world.salvdur,world.salvtrit,world.salvadam)
    rumpolicy = (True if world.rumsoddium == 4 else None)

    return render(request, 'policies_econ.html', {'result': result, 'rescosts':rescosts, 'world':world,
        'shownoob':shownoob, 'pvalues': v.production, 'shutterform': mineshutdownform(world),
        'showtrit':showtrit, 'showadam':showadam, 'rumpolicy':rumpolicy, 'rumsodmsg':rumsodmsg, 'salvagecost':salvagecost, 'salvagetext':salvagetext})


@login_required            ## DOMESTIC
@world_required
@noaction_required
def policies_domestic(request):

    # variable setup
    world = request.user.world
    gdp = world.gdp
    moregdp = 1.5 * world.gdp

    if world.econsystem == 1:
        scaling = 2
    elif world.econsystem == 0:
        scaling = 1.5
    elif world.econsystem == -1:
        scaling = 1

    citycost = (50*scaling if world.gdp <= 500 else (world.gdp/10)*scaling)

    result = None

    if request.method == 'POST':
        form = request.POST
        actions = False
        if "arrest" in form:
            if world.budget < 50:
                result = outcomes.nomoney()
            elif world.polsystem <= -80:
                result = outcomes.arrest('ArrestedAll')
            else:
                outcome = random.randint(1, 100)
                stab = utilities.attrchange(world.stability, 10)
                cont = utilities.attrchange(world.contentment, -10)
                polsys = utilities.attrchange(world.polsystem, -10)
                actions = {
                'budget': {'action': 'subtract', 'amount': 50},
                'stability': {'action': 'add', 'amount': stab},
                'contentment': {'action': 'add', 'amount': cont},
                'polsystem': {'action': 'add', 'amount': polsys},
                }
                if 95 < outcome <= 100:
                    rebels = utilities.attrchange(world.rebels, -5, zero=True)
                    actions.update({'rebels': {'action': 'subtract', 'amount': rebels}})
                result = outcomes.arrest(outcome)

        if "free" in form:
            if world.budget < 50:
                result = outcomes.nomoney()
            elif world.polsystem >= 60:
                result = outcomes.free('FreedAll')
            else:
                outcome = random.randint(1, 100)
                stab = utilities.attrchange(world.stability, -10)
                cont = utilities.attrchange(world.contentment, 10)
                polsys = utilities.attrchange(world.polsystem, 10)
                actions = {
                'budget': {'action': 'subtract', 'amount': 50},
                'stability': {'action': 'add', 'amount': stab},
                'contentment': {'action': 'add', 'amount': cont},
                'polsystem': {'action': 'add', 'amount': polsys},
                }
                if 80 < outcome <= 100:
                    rebels = utilities.attrchange(world.rebels, 5)
                    actions.update({'rebels': {'action': 'subtract', 'amount': rebels}})
                result = outcomes.free(outcome)

        if "martiallaw" in form:
            offwars = world.warattacker.all()
            defwars = world.wardefender.all()
            om = offwars.aggregate(m=Min('starttime'))
            dm = defwars.aggregate(m=Min('starttime'))
            omw = (v.now() if om['m'] is None else om['m'])
            dmw = (v.now() if dm['m'] is None else dm['m'])
            maxtime = (omw if omw < dmw else dmw)
            nexttime = v.now() + time.timedelta(days=5)

            if world.budget < 500:
                result = outcomes.nomoney()
            elif offwars.count() == 0 and defwars.count() == 0:
                result = outcomes.martiallaw('NotAtWar')
            elif world.polsystem <= -60:
                result = outcomes.martiallaw('Dictator')
            elif -60 < world.polsystem < -20:
                result = outcomes.martiallaw('AlreadyAdmiralty')
            elif world.timetonextadmiralty > v.now():
                timediff = world.timetonextadmiralty - v.now()
                result = outcomes.martiallaw('TooSoon', timediff)
            elif maxtime > v.now() - time.timedelta(days=1):
                timediff = maxtime - (v.now() - time.timedelta(days=1))
                result = outcomes.martiallaw('UnderTime', timediff)
            else:
                world.timetonextadmiralty = nexttime
                stab = utilities.attrchange(world.stability, 10)
                cont = utilities.attrchange(world.contentment, -20)
                actions = {
                'budget': {'action': 'subtract', 'amount': 500},
                'stability': {'action': 'subtract', 'amount': stab},
                'contentment': {'action': 'add', 'amount': cont},
                'polsystem': {'action': 'set', 'amount': -40},
                'timetonextadmiralty': {'action': 'set', 'amount': nexttime}
                }
                #utilities.martiallawadd(world)
                result = outcomes.martiallaw('Success')

        if "citybuilding" in form:
            if world.budget < citycost:
                result = outcomes.nomoney()
            else:
                outcome = random.randint(1, 100)
                cont = utilities.attrchange(world.contentment, 10)
                actions = {
                'budget': {'action': 'subtract', 'amount': D(citycost)},
                'contentment': {'action': 'add', 'amount': cont},
                }
                if 95 < outcome <= 100:
                    qol = utilities.attrchange(world.qol, 4)
                    actions.update({'qol': {'action': 'add', 'amount': qol}})
                result = outcomes.citybuilding(outcome)

        if "literacy" in form:
            if world.budget < world.gdp:
                result = outcomes.nomoney()
            elif world.qol == 100:
                result = outcomes.maxqol()
            else:
                qol = utilities.attrchange(world.qol, 20)
                contentment = utilities.attrchange(world.contentment, 5)            
                actions = {
                'contentment': {'action': 'add', 'amount': contentment},
                'qol': {'action': 'add', 'amount': qol},
                'budget': {'action': 'subtract', 'amount': world.gdp},
                }
                result = outcomes.literacy()

        if "healthcare" in form:
            if world.budget < ((world.gdp)*1.5):
                result = outcomes.nomoney()
            elif world.qol == 100:
                result = outcomes.maxqol()
            else:
                qol = utilities.attrchange(world.qol, 40)
                contentment = utilities.attrchange(world.contentment, 10)
                actions = {
                'contentment': {'action': 'add', 'amount': contentment},
                'qol': {'action': 'add', 'amount': qol},
                'budget': {'action': 'subtract', 'amount': D(world.gdp * 1.5)},
                }
                result = outcomes.healthcare()
        if actions:
            utilities.atomic_world(world.pk, actions)
            world.refresh_from_db()

    money = world.budget
    return render(request, 'policies_domestic.html', {'result': result, 'GDP': gdp, 'moreGDP': moregdp, 'citycost': citycost, 'money':money})


@login_required            ## DIPLOMACY
@world_required
@noaction_required
def policies_diplomacy(request):

    # variable setup
    world = request.user.world
    result = None
    if Spy.objects.filter(owner=world, location=world).count() == 0:
        spyform = None
    else:
        spyform = SelectSpyForm(world)

    if request.method == 'POST':
        form = request.POST
        actions = False
        if "createfederation" in form:
            if world.alliance != None:
                result = outcomes.createfederation('AlreadyAllied')
            elif world.alliancepaid:
                return redirect('new_alliance')
            else:
                if world.budget < 200:
                    result = outcomes.nomoney()
                else:
                    actions = {
                    'budget': {'action': 'subtract', 'amount': 200},
                    'alliancepaid': {'action': 'set', 'amount': True}
                    }
                    utilities.atomic_world(world.pk, actions)
                    return redirect('new_alliance')

        if "trainspy" in form:
            name = form['spyname']
            if world.budget < 500:
                result = outcomes.nomoney()
            elif Spy.objects.filter(owner=world).count() >= 5:
                result = outcomes.trainspy('TooMany')
            elif len(name) > 10:
                result = outcomes.trainspy('TooLong')
            else:
                actions = {'budget': {'action': 'subtract', 'amount': 500}}
                spy = Spy.objects.create(owner=world, location=world, name=name)
                if world.sector == 'draco':
                    if world.millevel >= v.millevel('dre'):
                        spy.infiltration = spy.propaganda = spy.gunrunning =  spy.intelligence = spy.sabotage = spy.counterint = 4
                    else:
                        spy.infiltration = spy.propaganda = spy.gunrunning =  spy.intelligence = spy.sabotage = spy.counterint = 2
                spy.nextaction = v.now() + time.timedelta(hours=4)
                spy.save()
                result = outcomes.trainspy('Success')

        if "counterintel" in form:
            form = SelectSpyForm(world, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                spyid = data['spyselect']
                try:
                    spy = Spy.objects.get(pk=spyid)
                except ObjectDoesNotExist:
                    result = "There is no such spy!"
                else:
                    if world.budget < 100:
                        result = outcomes.nomoney()
                    elif spy.owner != world:
                        result = "This spy does not belong to your intelligence services!"
                    elif spy.location != world:
                        result = "This spy is not at your home world!"
                    elif spy.nextaction > v.now():
                        result = "This spy is currently recovering and unavailable for missions."
                    else:
                        actions = {'budget': {'action': 'subtract', 'amount': 100}}
                        killed = 0
                        listkilled = []
                        enemyspies = list(Spy.objects.filter(location=world).exclude(owner=world))
                        for enspy in enemyspies:
                            chance = random.randint(1, 100)
                            if 20 + spy.counterint - enspy.timespent >= chance:
                                killed += 1
                                listkilled.append(enspy)
                                reveal, x = utilities.reveal(enspy)

                                htmldata = news.counterintkilled(enspy, world)
                                NewsItem.objects.create(target=enspy.owner, content=htmldata)

                                enspy.delete()

                        spy.nextaction = v.now() + time.timedelta(hours=8)
                        if killed > 0:
                            spy.counterint += 1
                        spy.save()

                        result = outcomes.counterintel(listkilled)
            else:
                result = "You have no spies available!"
        if actions:
            utilities.atomic_world(world.pk, actions)
            world.refresh_from_db()
    money = world.budget
    return render(request, 'policies_diplomacy.html', {'result': result, 'money':money, 'spyform':spyform})


@login_required            ## MILITARY
@world_required
@noaction_required
def policies_military(request):

    # variable setup, stuff needed to process POST data
    world = request.user.world
    result = indefwar = rumsodmsg = None
    shipdata = v.shipcosts(world.sector)
    rebelfuelcost = 0
    if request.method == 'POST':
        form = request.POST
        actions = False        #if the nigga wants to build ships
        if 'build' in form:
            shiptype = form['build']
            form = shipbuildform(world, data={shiptype: form[shiptype]})
            if form.is_valid():
                amount = form.cleaned_data[shiptype]
                ship = (shiptype if amount > 1 else shiptype[:-1]) #shipname, if >1 then plural
                if amount == 0:
                    result = "Can't build 0 %s!" % ship.replace('_', ' ')
                else:
                    #make sure he can (or she) can afford it
                    results = utilities.costcheck(world, form.cleaned_data)
                    if results['status'] is True: #player can afford it
                        actions = {
                        'budget': {'action': 'subtract', 'amount': D(results['cost']['geu'])},
                        'duranium': {'action': 'subtract', 'amount': results['cost']['duranium']},
                        'tritanium': {'action': 'subtract', 'amount': results['cost']['tritanium']},
                        'adamantium': {'action': 'subtract', 'amount': results['cost']['adamantium']},
                        'productionpoints': {'action': 'subtract', 'amount': results['cost']['productionpoints']}
                        }
                        #queue merges with build fleet at turn change
                        queue = shipqueue(world=world, fleet=world.preferences.buildfleet)
                        queue.__dict__[shiptype] = amount
                        current_time = v.now()
                        if current_time.hour > 12:
                            hours = 24 - current_time.hour - 1
                            minutes = 60 - current_time.minute
                        else:
                            hours = 12 - current_time.hour - 1
                            minutes = 60 - current_time.minute
                        outcometime = current_time + time.timedelta(hours=hours, minutes=minutes)
                        ship = ship.replace('_', ' ')
                        task = Task.objects.create(target=world, content=taskdata.buildship(ship, amount), datetime=outcometime)
                        queue.task = task
                        queue.save()
                        result = "%s %s are building" % (amount, ship)
                    else:
                        result = "You can't afford to build %s %s!" % (amount, ship.replace('_', ' '))      

        if "research" in form:
            form = ResearchForm(request.POST)
            if form.is_valid():
                next_tier = v.tiers[v.tiers.index(world.techlevel)+1]
                rdcost = shipdata[next_tier.replace(' ', '_').lower() + 's']['research']
                durcost = rdcost['duranium']
                try:
                    tritcost = rdcost['tritanium']
                except:
                    tritcost = 0
                try:
                    adamcost = rdcost['adamantium']
                except:
                    adamcost = 0
                data = form.cleaned_data
                amount = data['researchamount']
                if amount < 0:
                    result = 'Enter a positive integer.'
                elif world.techlevel == "dreadnought":
                    result = 'You have researched all ship types already!'
                elif world.budget < amount:
                    result = outcomes.nomoney()
                elif durcost > world.duranium:
                    result = outcomes.research('NoDur')
                elif tritcost > world.tritanium:
                    result = outcomes.research('NoTrit')
                elif adamcost > world.adamantium:
                    result = outcomes.research('NoAdam')
                elif world.turnresearched:
                    result = outcomes.research('TooSoon')
                elif amount > 3*world.gdp:
                    result = outcomes.research('TooMuch')
                else:
                    actions = {
                    'budget': {'action': 'subtract', 'amount': amount},
                    'duranium': {'action': 'subtract', 'amount': durcost},
                    'tritanium': {'action': 'subtract', 'amount': tritcost},
                    'adamantium': {'action': 'subtract', 'amount': adamcost},
                    'turnresearched': {'action': 'set', 'amount': True},
                    'budget': {'action': 'subtract', 'amount': amount},
                    }
                    if world.sector == 'draco':
                        amount = int(amount*1.25)
                    message = outcomes.researchtext(world, amount)
                    actions.update({'millevel': {'action': 'add', 'amount': amount}})
                    result = outcomes.research('Success', result=message)

        if "moveship" in form:
            form = fleetwarpform(world, request.POST)
            if form.is_valid(): #form checks practically everything but warpcost
                warpfleet = fleet.objects.get(pk=form.cleaned_data['fleet'])
                if warpfleet.enoughfuel():
                    tgtsector = form.cleaned_data['destination']
                    actions = {'warpfuel': {'action': 'subtract', 'amount': warpfleet.fuelcost()}}
                    taskcontent = taskdata.warpfleet(warpfleet.name, warpfleet.sector, tgtsector)
                    delay = (4 if tgtsector == warpfleet.sector else 8)
                    outcometime = v.now() + time.timedelta(minutes=2)
                    task = Task.objects.create(target=world, content=taskcontent, datetime=outcometime)
                    newtask.fleet_warp.apply_async(args=(warpfleet.pk, warpfleet.name, tgtsector, task.pk), eta=outcometime)
                    result = "%s bugs out and is warping to %s" % (warpfleet.name, tgtsector)
                    #actually altering data goes last
                    utilities.atomic_fleet(warpfleet.pk, ['warp'])
                else:
                    result = "Not enough warpfuel, %s needs %s more warpfuel to warp!" % \
                        (warpfleet.name, (warpfleet.fuelcost() - world.warpfuel))

        if "train" in form:
            form = trainfleetform(world, form)
            if form.is_valid():
                targetfleet = form.cleaned_data['fleet']
                if world.budget < targetfleet.trainingcost():
                    result = outcomes.nomoney()
                elif targetfleet.training >= targetfleet.maxtraining():
                    result = outcomes.training('AtMax')
                else:
                    actions = {
                    'budget': {'action': 'subtract', 'amount': targetfleet.trainingcost()},
                    }
                    utilities.atomic_fleet(targetfleet.pk, {'train': True})

        if "buildshipyard" in form:
            if world.budget < 500:
                result = outcomes.nomoney()
            elif world.duranium < 5:
                result = outcomes.notenoughduranium()
            else:
                actions = {
                'budget': {'action': 'subtract', 'amount': 500},
                'duranium': {'action': 'subtract', 'amount': 1},
                'shipyards': {'action': 'add', 'amount': 1},
                }
                result = outcomes.shipyards('Success')

        if "attackrebels" in form:
            fleets = world.controlled_fleets.all()
            worldpower = utilities.militarypower(world, world.sector)
            fuelcost = int(0.1 * utilities.warpfuelcost(worldlist))
            if world.budget < 10:
                result = outcomes.nomoney()
            elif world.rebels == 0:
                result = outcomes.norebels()
            elif world.warpfuel < fuelcost:
                result = 'You do not have enough warpfuel to hunt down the rebels!'
            elif worldpower == 0:
                result = 'You do not have a fleet to attack the rebels with!'
            else:
                world.budget = F('budget') - 10
                world.warpfuel = F('warpfuel') - fuelcost

                totworldpower = utilities.powerallmodifiers(world, world.sector)

                rebelpower = 0
                for f in fleets:
                    rebelpower += f.basepower() # sum of total fleet power

                outcome = random.randint(1, 100)
                if (1 <= outcome < 5) or (30 < outcome <= 100):
                    if 1 <= world.rebels < 20:
                        rebelpower = 0.01*rebelpower
                    elif 20 <= world.rebels < 40:
                        rebelpower = 0.02*rebelpower
                    elif 40 <= world.rebels < 60:
                        rebelpower = 0.03*rebelpower
                    elif 60 <= world.rebels < 80:
                        rebelpower = 0.04*rebelpower
                    elif world.rebels >= 80:
                        rebelpower = 0.05*rebelpower
                    dmg = utilities.war_result(rebelpower, totworldpower, worldpower)
                    utilities.warloss_byregion(world, world.sector, deflosses)

                if 30 < outcome <= 100:
                    utilities.rebelschange(world, -5)
                elif 1 <= outcome <= 5:
                    utilities.rebelschange(world, 5)

                utilities.wearinesschange(world, world.sector, -2)

                world.save(update_fields=['budget','warpfuel'])

                result = news.rebelresult(outcome, deflosses)

        if "rumsodmil" in form:
            targetname = form['targetname']
            try:
                target = World.objects.get(world_name=targetname)
            except ObjectDoesNotExist:
                result = 'There is no such world by that name!'
            else:
                if world.rumsoddium != 4:
                    result = 'You do not have enough rumsoddium for the ritual!'
                else:
                    target.gdp = F('gdp') - int(target.gdp/2)
                    target.budget = F('budget') - D(target.budget/2)
                    target.warpfuel = F('warpfuel') - int(target.warpfuel/2)
                    target.duranium = F('duranium') - int(target.duranium/2)
                    target.tritanium = F('tritanium') - int(target.tritanium/2)
                    target.adamantium = F('adamantium') - int(target.adamantium/2)
                    world.rumsoddium = 0
                    world.save(update_fields=['rumsoddium'])
                    target.save(update_fields=['gdp','budget','warpfuel','duranium','tritanium','adamantium'])
                    rumsodmsg = v.rumsodmilitary
                    htmldata = news.rumsodmilitaryreceive(world)
                    NewsItem.objects.create(target=target, content=htmldata)
                    utilities.rumsoddiumhandout()

        if "buildflagship" in form:
            form = PersonalShipForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                if world.flagshiptype != 0:
                    result = outcomes.personalship('Already')
                elif shiptype not in [1,2,3]:
                    result = 'Invalid shiptype selected!'
                elif world.budget < 500:
                    result = outcomes.nomoney()
                elif (world.shipyards - world.shipyardsinuse) < 5:
                    result = outcomes.notenoughshipyards()
                elif world.duranium < 20:
                    result = outcomes.notenoughduranium()
                else:
                    current_time = v.now()
                    if current_time.hour > 12:
                        hours = 24 - current_time.hour - 1
                        minutes = 60 - current_time.minute
                    else:
                        hours = 12 - current_time - 1
                        minutes = 60 - current_time.minute
                    outcometime = v.now() + time.timedelta(hours=hours, minutes=minutes)
                    world.budget = F('budget') - D(500)
                    world.duranium = F('duranium') - 20
                    world.productionpoints = F('shipyardsinuse') + 25
                    world.flagshipbuild = True
                    world.save(update_fields=['budget','duranium','productionpoints','flagshipbuild'])
                    taskdetails = taskdata.buildpersonalship(shiptype)
                    task = Task(target=world, content=taskdetails, datetime=outcometime)
                    task.save()

                    newtask.buildpersonalship.apply_async(args=(world.pk, task.pk, shiptype), eta=outcometime)
                    result = outcomes.personalship('Success', shiptype)

        if "scuttleflagship" in form:
            if world.flagshiptype == 0:
                result = 'You do not have a flagship to scuttle!'
            else:
                utilities.flagshipreset(world)
                result = 'You scuttled your flagship.'

        elif "setfleetprefs" in form:
            form = buildlocationform(world, request.POST)
            if form.is_valid():
                prefs = world.preferences
                prefs.buildfleet = form.cleaned_data['buildchoice']
                prefs.recievefleet = form.cleaned_data['recievechoice']
                prefs.save()
                result = "Fleet preferences successfully updated"

        if actions:
            utilities.atomic_world(world.pk, actions)
            world.refresh_from_db()
    if world.wardefender.count() > 0:
        indefwar = True
    #create context dictionary with needed variables instead of fuckhuge return dict
    costs = []
    ids = []
    for f in world.fleets.all().filter(sector=world.sector):
        costs.append(f.trainingcost())
        ids.append(f.pk)

    context = {
        'costs': costs,
        'ids': ids,
        'result':result,
        'researchform': ResearchForm(),
        'buildtoform': buildlocationform(world, initial={'buildchoice': world.preferences.buildfleet.pk,
                                                         'recievechoice': world.preferences.recievefleet.pk}),
        'moveform': fleetwarpform(world),
        'prefs': world.shipsortprefs,
        'buildlist': display.milpolicydisplay(world),
        'rumpolicy':(True if world.rumsoddium == 4 else None),
        'rumsodmsg':rumsodmsg,
        'indefwar': (True if world.wardefender.count() > 0 else False),
        'rebelfuelcost':rebelfuelcost,
        'displayresearch': (True if v.tiers.index(world.techlevel) is len(v.tiers) else False),
        'result':result,
        'rumsodmsg':rumsodmsg,
        'world': world,
        'trainform': trainfleetform(world),
    }
    if world.techlevel != "Dreadnought":
        next_tier = v.tiers[v.tiers.index(world.techlevel)+1]
        rdcost = shipdata[next_tier.replace(' ', '_').lower() + 's']['research']
        context.update({'costmsg': rdcost, 'shiptext': next_tier})

    return render(request, 'policies_military.html', context)
