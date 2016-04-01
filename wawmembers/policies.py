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
    world = World.objects.get(worldid=request.user.id)

    result = rumsodmsg = None
    warpcost, durcost, tritcost, adamcost, rescost = utilities.rescosts(world)
    salvagecost = 2 * (world.salvdur + world.salvtrit + world.salvadam)
    salvagecost = (100 if salvagecost < 100 else salvagecost)
    indcap, indcost = v.inddetails(world)

    shownoob = (True if world.gdp <= 115 else None)
    showtrit = (True if world.millevel >= v.millevel('lcr') else None)
    showadam = (True if world.millevel >= v.millevel('hcr') else None)

    if request.method == 'POST':
        form = request.POST

        if "buildresource" in form:
            if world.budget < rescost:
                result = outcomes.nomoney()
            elif Agreement.objects.filter(sender=world).count() == 130:
                result = outcomes.buildresource('TooMany')
            else:
                world.budget = F('budget') - rescost
                world.save(update_fields=['budget'])
                Agreement.objects.create(sender=world, receiver=world, order=0, resource=world.resource)
                result = outcomes.buildresource('Success')

        if "indprogram" in form:
            value = form['indprogramval']
            if not utilities.checkno(value, True):
                result = outcomes.indprogram('NoNum')
            elif int(value) > indcap:
                result = outcomes.indprogram('Above')
            else:
                world.industrialprogram = value
                world.save(update_fields=['industrialprogram'])
                result = outcomes.indprogram('Success')

        if "noobgrowthpolicy" in form:
            if world.budget < 70:
                result = outcomes.nomoney()
            elif not shownoob:
                result = outcomes.noobgrowth('TooRich')
            elif world.growth >= 100:
                result = outcomes.toomuchgrowth()
            else:
                world.budget = F('budget') - 70
                world.growth = F('growth') + 2
                world.save(update_fields=['budget','growth'])
                result = outcomes.noobgrowth('Success')

        if "buybonds" in form:
            if world.budget < 100:
                result = outcomes.nomoney()
            elif world.econsystem == -1:
                result = outcomes.buybonds('NotFreeorMixed')
            elif world.growth >= 100:
                result = outcomes.toomuchgrowth()
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - 100
                if outcome > 50:
                    world.growth = F('growth') + 2
                world.save(update_fields=['budget','growth'])
                result = outcomes.buybonds(outcome)

        if "impmodel" in form:
            if world.budget < 100:
                result = outcomes.nomoney()
            elif world.econsystem != -1:
                result = outcomes.impmodel('NotCentralPlanning')
            elif world.growth >= 100:
                result = outcomes.toomuchgrowth()
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - 100
                if outcome > 30:
                    world.growth = F('growth') + 2
                world.save(update_fields=['budget','growth'])
                result = outcomes.impmodel(outcome)

        if "qeasing" in form:
            if world.budget < 50:
                result = outcomes.nomoney()
            elif world.stability < -80:
                result = outcomes.qeasing('LowStab')
            elif world.growth >= 100:
                result = outcomes.toomuchgrowth()
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - 50
                utilities.stabilitychange(world, -5)
                if outcome > 50:
                    world.growth = F('growth') + 2
                world.save(update_fields=['budget','growth'])
                result = outcomes.qeasing(outcome)

        if "forcedlabour" in form:
            if world.polsystem > -60:
                result = outcomes.forcedlabour('NotDictatorship')
            elif world.stability < -80:
                result = outcomes.forcedlabour('StabilityTooLow')
            else:
                outcome = random.randint(1, 100)
                utilities.contentmentchange(world, -10)
                utilities.stabilitychange(world, -5)
                if 15 < outcome <= 100:
                    world.growth = F('growth') + 5
                if 1 <= outcome <= 5:
                    utilities.rebelschange(world, 10)
                world.save(update_fields=['growth'])
                result = outcomes.forcedlabour(outcome)

        if "nationalise" in form:
            if world.econsystem == -1:
                result = outcomes.nationalise('NotFreeOrMixed')
            elif world.econchanged:
                result = outcomes.nationalise('Already')
            else:
                if world.econsystem == 0:
                    for agreement in list(Agreement.objects.filter(sender=world)):
                        if agreement.receiver.econsystem == 1: # revert agreements if opposite system
                            AgreementLog.objects.create(owner=agreement.receiver, target=world, resource=world.resource, logtype=2)
                            agreement.receiver = world
                            agreement.save(update_fields=['receiver'])
                world.econsystem = F('econsystem') - 1
                utilities.stabilitychange(world, -20)
                world.econchanged = True
                world.save(update_fields=['econsystem','econchanged'])
                result = outcomes.nationalise('Success')

        if "privatise" in form:
            if world.econsystem == 1:
                result = outcomes.privatise('NotCPorMixed')
            elif world.econchanged:
                result = outcomes.nationalise('Already')
            else:
                if world.econsystem == -1 and world.industrialprogram > 1200:
                    world.industrialprogram = 1200
                if world.econsystem == 0:
                    if world.industrialprogram > 0:
                        world.industrialprogram = 0
                    for agreement in list(Agreement.objects.filter(sender=world)):
                        if agreement.receiver.econsystem == -1: # revert agreements if opposite system
                            AgreementLog.objects.create(owner=agreement.receiver, target=world, resource=world.resource, logtype=2)
                            agreement.receiver = world
                            agreement.save(update_fields=['receiver'])
                world.econsystem = F('econsystem') + 1
                utilities.stabilitychange(world, -20)
                world.econchanged = True
                world.save(update_fields=['econsystem','econchanged','industrialprogram'])
                result = outcomes.privatise('Success')

        if "buildfuelrefinery" in form:
            if world.budget < warpcost:
                result = outcomes.nomoney()
            else:
                world.budget = F('budget') - warpcost
                if 5 < random.randint(1, 100) <= 100:
                    world.warpfuelprod = F('warpfuelprod') + 10
                    result = outcomes.buildfuelrefinery('Success')
                else:
                    result = outcomes.buildfuelrefinery('Failure')
                world.save(update_fields=['budget','warpfuelprod'])

        if "prospectduranium" in form:
            if world.budget < durcost:
                result = outcomes.nomoney()
            else:
                world.budget = F('budget') - durcost
                regionmod = (10 if world.region == 'C' else 40)
                if regionmod < random.randint(1, 100) <= 100:
                    world.duraniumprod = F('duraniumprod') + 3
                    result = outcomes.prospectduranium('Success')
                else:
                    result = outcomes.prospectduranium('Failure')
                world.save(update_fields=['budget','duraniumprod'])

        if "prospecttritanium" in form:
            if world.budget < tritcost:
                result = outcomes.nomoney()
            elif showtrit is None:
                result = outcomes.needhigherlevel()
            else:
                world.budget = F('budget') - tritcost
                regionmod = (20 if world.region == 'C' else 50)
                if regionmod < random.randint(1, 100) <= 100:
                    world.tritaniumprod = F('tritaniumprod') + 2
                    result = outcomes.prospecttritanium('Success')
                else:
                    result = outcomes.prospecttritanium('Failure')
                world.save(update_fields=['budget','tritaniumprod'])

        if "prospectadamantium" in form:
            if world.budget < adamcost:
                result = outcomes.nomoney()
            elif showadam is None:
                result = outcomes.needhigherlevel()
            else:
                world.budget = F('budget') - adamcost
                regionmod = (40 if world.region == 'C' else 70)
                if regionmod < random.randint(1, 100) <= 100:
                    world.adamantiumprod = F('adamantiumprod') + 1
                    result = outcomes.prospectadamantium('Success')
                else:
                    result = outcomes.prospectadamantium('Failure')
                world.save(update_fields=['budget','adamantiumprod'])

        if "salvagemission" in form:
            if world.budget < salvagecost:
                result = outcomes.nomoney()
            elif world.turnsalvaged:
                result = outcomes.salvagemission('AlreadySalvaged')
            elif world.salvdur + world.salvtrit + world.salvadam == 0:
                result = outcomes.salvagemission('NoSalvage')
            else:
                world.budget = F('budget') - salvagecost
                salvmin = (70 if world.region == 'C' else 60)
                salvmax = (80 if world.region == 'C' else 70)
                dur = int(round(world.salvdur * random.randint(salvmin, salvmax) / 100.0))
                trit = int(round(world.salvtrit * random.randint(salvmin, salvmax) / 100.0))
                adam = int(round(world.salvadam * random.randint(salvmin, salvmax) / 100.0))
                world.salvdur = F('salvdur') - dur
                world.duranium = F('duranium') + dur
                world.salvtrit = F('salvtrit') - trit
                world.tritanium = F('tritanium') + trit
                world.salvadam = F('salvadam') - adam
                world.adamantium = F('adamantium') + adam
                world.turnsalvaged = True
                result = outcomes.salvagemission([dur,trit,adam])
                world.save(update_fields=['budget','salvdur','salvtrit','salvadam','duranium','tritanium',
                    'adamantium','turnsalvaged'])

        if "rumsodecon" in form:
            if world.rumsoddium != 4:
                result = 'You do not have enough rumsoddium for the ritual!'
            else:
                world.gdp = F('gdp') + world.gdp
                world.budget = F('budget') + world.budget - 10
                world.warpfuel = F('warpfuel') + world.warpfuel
                world.duranium = F('duranium') + world.duranium
                world.tritanium = F('tritanium') + world.tritanium
                world.adamantium = F('adamantium') + world.adamantium
                world.rumsoddium = 0
                world.save(update_fields=['gdp','budget','warpfuel','duranium','tritanium','adamantium','rumsoddium'])
                rumsodmsg = v.rumsodeconomy
                utilities.rumsoddiumhandout()

    world = World.objects.get(pk=world.pk)
    warpcost, durcost, tritcost, adamcost, rescost = utilities.rescosts(world)
    salvagecost = 2 * (world.salvdur + world.salvtrit + world.salvadam)
    salvagecost = (100 if salvagecost < 100 else salvagecost)
    salvagetext = news.salvagetext(world.salvdur,world.salvtrit,world.salvadam)
    indcap, indcost = v.inddetails(world)
    rumpolicy = (True if world.rumsoddium == 4 else None)

    return render(request, 'policies_econ.html', {'result': result, 'duraniumcost':durcost, 'warpfuelcost':warpcost, 'world':world,
        'tritaniumcost':tritcost, 'adamantiumcost':adamcost, 'shownoob':shownoob, 'rescost':rescost, 'indcap':indcap, 'indcost':indcost,
        'showtrit':showtrit, 'showadam':showadam, 'rumpolicy':rumpolicy, 'rumsodmsg':rumsodmsg, 'salvagecost':salvagecost, 'salvagetext':salvagetext})


@login_required            ## DOMESTIC
@world_required
@noaction_required
def policies_domestic(request):

    # variable setup
    world = World.objects.get(worldid=request.user.id)
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

        if "arrest" in form:
            if world.budget < 50:
                result = outcomes.nomoney()
            elif world.polsystem <= -80:
                result = outcomes.arrest('ArrestedAll')
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - 50
                utilities.stabilitychange(world, 10)
                utilities.contentmentchange(world, -10)
                utilities.polsystemchange(world, -10)
                if 95 < outcome <= 100:
                    utilities.rebelschange(world, -5)
                world.save(update_fields=['budget'])
                result = outcomes.arrest(outcome)

        if "free" in form:
            if world.budget < 50:
                result = outcomes.nomoney()
            elif world.polsystem >= 60:
                result = outcomes.free('FreedAll')
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - 50
                utilities.stabilitychange(world, -10)
                utilities.contentmentchange(world, 10)
                utilities.polsystemchange(world, 10)
                if 80 < outcome <= 100:
                    utilities.rebelschange(world, 5)
                world.save(update_fields=['budget'])
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
                world.budget = F('budget') - 500
                world.polsystem = -40
                world.timetonextadmiralty = nexttime
                utilities.stabilitychange(world, 10)
                utilities.contentmentchange(world, -20)
                utilities.martiallawadd(world)
                world.save(update_fields=['budget','polsystem'])
                result = outcomes.martiallaw('Success')

        if "citybuilding" in form:
            if world.budget < citycost:
                result = outcomes.nomoney()
            else:
                outcome = random.randint(1, 100)
                world.budget = F('budget') - citycost
                utilities.contentmentchange(world, 10)
                if 95 < outcome <= 100:
                    utilities.qolchange(world, 4)
                world.save(update_fields=['budget'])
                result = outcomes.citybuilding(outcome)

        if "literacy" in form:
            if world.budget < world.gdp:
                result = outcomes.nomoney()
            elif world.qol == 100:
                result = outcomes.maxqol()
            else:
                world.budget = F('budget') - world.gdp
                utilities.qolchange(world, 20)
                utilities.contentmentchange(world, 5)
                world.save(update_fields=['budget'])
                result = outcomes.literacy()

        if "healthcare" in form:
            if world.budget < ((world.gdp)*1.5):
                result = outcomes.nomoney()
            elif world.qol == 100:
                result = outcomes.maxqol()
            else:
                world.budget = F('budget') - D((world.gdp)*1.5)
                utilities.qolchange(world, 40)
                utilities.contentmentchange(world, 10)
                world.save(update_fields=['budget'])
                result = outcomes.healthcare()

    world = World.objects.get(pk=world.pk)
    money = world.budget
    return render(request, 'policies_domestic.html', {'result': result, 'GDP': gdp, 'moreGDP': moregdp, 'citycost': citycost, 'money':money})


@login_required            ## DIPLOMACY
@world_required
@noaction_required
def policies_diplomacy(request):

    # variable setup
    result = None
    world = World.objects.get(worldid=request.user.id)
    if Spy.objects.filter(owner=world, location=world).count() == 0:
        spyform = None
    else:
        spyform = SelectSpyForm(world)

    if request.method == 'POST':
        form = request.POST

        if "createfederation" in form:
            if world.alliance != None:
                result = outcomes.createfederation('AlreadyAllied')
            elif world.alliancepaid:
                return redirect('new_alliance')
            else:
                if world.budget < 200:
                    result = outcomes.nomoney()
                else:
                    world.budget = F('budget') - 200
                    world.alliancepaid = True
                    world.save(update_fields=['budget','alliancepaid'])
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
                world.budget = F('budget') - 500
                world.save(update_fields=['budget'])
                spy = Spy(owner=world, location=world, name=name)
                spy.save()
                if world.region == 'D':
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
                        world.budget = F('budget') - 100
                        world.save(update_fields=['budget'])
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

    world = World.objects.get(pk=world.pk)
    money = world.budget
    return render(request, 'policies_diplomacy.html', {'result': result, 'money':money, 'spyform':spyform})


@login_required            ## MILITARY
@world_required
@noaction_required
def policies_military(request):

    # variable setup
    world = World.objects.get(worldid=request.user.id)

    result = indefwar = rumsodmsg = None

    datafig = utilities.shipdata(world.region, 1)
    datacor = utilities.shipdata(world.region, 2)
    datalcr = utilities.shipdata(world.region, 3)
    datades = utilities.shipdata(world.region, 4)
    datafri = utilities.shipdata(world.region, 5)
    datahcr = utilities.shipdata(world.region, 6)
    databcr = utilities.shipdata(world.region, 7)
    databsh = utilities.shipdata(world.region, 8)
    datadre = utilities.shipdata(world.region, 9)

    displaybuilds = [False for i in range(9)]

    if world.millevel >= v.millevel('dre'):
        limit = 9
    elif world.millevel >= v.millevel('bsh'):
        limit = 8
    elif world.millevel >= v.millevel('bcr'):
        limit = 7
    elif world.millevel >= v.millevel('hcr'):
        limit = 6
    elif world.millevel >= v.millevel('fri'):
        limit = 5
    elif world.millevel >= v.millevel('des'):
        limit = 4
    elif world.millevel >= v.millevel('lcr'):
        limit = 3
    elif world.millevel >= v.millevel('cor'):
        limit = 2
    else:
        limit = 1
    for index, value in enumerate(displaybuilds[:limit]):
        displaybuilds[index] = True

    displayresearch = True
    if displaybuilds[8]:
        displayresearch = shiptext = costmsg = None
    elif displaybuilds[7]:
        shiptext = 'dreadnought'
        costmsg = '10 adamantium, 20 tritanium, 30 duranium'
        durcost = 30
        tritcost = 20
        adamcost = 10
    elif displaybuilds[6]:
        shiptext = 'battleship'
        costmsg = '5 adamantium, 15 tritanium, 25 duranium'
        durcost = 25
        tritcost = 15
        adamcost = 5
    elif displaybuilds[5]:
        shiptext = 'battlecruiser'
        costmsg = '2 adamantium, 12 tritanium, 20 duranium'
        durcost = 20
        tritcost = 12
        adamcost = 2
    elif displaybuilds[4]:
        shiptext = 'heavy cruiser'
        costmsg = '8 tritanium, 16 duranium'
        durcost = 16
        tritcost = 8
        adamcost = 0
    elif displaybuilds[3]:
        shiptext = 'frigate'
        costmsg = '4 tritanium, 12 duranium'
        durcost = 12
        tritcost = 4
        adamcost = 0
    elif displaybuilds[2]:
        shiptext = 'destroyer'
        costmsg = '2 tritanium, 8 duranium'
        durcost = 8
        tritcost = 2
        adamcost = 0
    elif displaybuilds[1]:
        shiptext = 'light cruiser'
        costmsg = '4 duranium'
        durcost = 4
        tritcost = 0
        adamcost = 0
    else:
        shiptext = 'corvette'
        costmsg = '2 duranium'
        durcost = 2
        tritcost = 0
        adamcost = 0

    currenth, maximumh = utilities.trainingstatus(world, world.region)
    trainingcosth = utilities.trainingcost(world, world.region)

    currents, maximums = utilities.trainingstatus(world, 'S')
    trainingcosts = utilities.trainingcost(world, 'S')

    if world.wardefender.count() > 0:
        indefwar = True

    shiplist = utilities.regionshiplist(world, world.region)
    rebelfuelcost = int(0.1 * utilities.warpfuelcost(shiplist))

    if request.method == 'POST':
        form = request.POST

        if "buildfighter" in form:
            amount = form['amountfig']
            result = utilities.generalbuild(world, 1, amount)

        if "buildcorvette" in form and displaybuilds[1]:
            amount = form['amountcor']
            result = utilities.generalbuild(world, 2, amount)

        if "buildlightcruiser" in form and displaybuilds[2]:
            amount = form['amountlcr']
            result = utilities.generalbuild(world, 3, amount)

        if "builddestroyer" in form and displaybuilds[3]:
            amount = form['amountdes']
            result = utilities.generalbuild(world, 4, amount)

        if "buildfrigate" in form and displaybuilds[4]:
            amount = form['amountfri']
            result = utilities.generalbuild(world, 5, amount)

        if "buildheavycruiser" in form and displaybuilds[5]:
            amount = form['amounthcr']
            result = utilities.generalbuild(world, 6, amount)

        if "buildbattlecruiser" in form and displaybuilds[6]:
            amount = form['amountbcr']
            result = utilities.generalbuild(world, 7, amount)

        if "buildbattleship" in form and displaybuilds[7]:
            amount = form['amountbsh']
            result = utilities.generalbuild(world, 8, amount)

        if "builddreadnought" in form and displaybuilds[8]:
            amount = form['amountdre']
            result = utilities.generalbuild(world, 9, amount)

        if "buildships" in form:
            listships = form['buildquantities'].split(',')
            successes = 0
            texts = []
            for shiptype, amount in enumerate(listships):
                world = World.objects.get(pk=world.pk)
                if displaybuilds[shiptype]:
                    result = utilities.generalbuild(world, shiptype+1, amount)
                    if 'You start' in result:
                        successes += 1
                        texts.append(' %s %s,' % (amount, utilities.resname(shiptype+11, amount, True)))

            if successes > 0:
                toreturn = 'You start construction of'
                if successes > 1:
                    for text in texts[:-1]:
                        toreturn += text
                    toreturn += ' and'
                    toreturn += texts[-1]
                else:
                    for text in texts:
                        toreturn += text

                result = toreturn[:-1]
                result += '.'
            else:
                result = 'You cannot build the ships you selected!'

        if "buildfreighter" in form:
            amount = form['amountfre']
            if not utilities.checkno(amount):
                result = "Enter a positive integer."
            else:
                amount = int(amount)
                cost = (85 if world.region == 'B' else 100)
                dur = (4 if world.region == 'B' else 5)
                if world.budget < D(cost*amount):
                    result = outcomes.nomoney()
                elif (world.shipyards - world.shipyardsinuse) < 2*amount:
                    result = outcomes.notenoughshipyards()
                elif world.duranium < dur*amount:
                    result = outcomes.notenoughduranium()
                else:
                    outcometime = v.now() + time.timedelta(hours=2)
                    world.budget = F('budget') - D(cost*amount)
                    world.duranium = F('duranium') - dur*amount
                    world.shipyardsinuse = F('shipyardsinuse') + 2*amount
                    world.save(update_fields=['budget','duranium','shipyardsinuse'])
                    taskdetails = taskdata.buildfreighter(amount)
                    task = Task(target=world, content=taskdetails, datetime=outcometime)
                    task.save()

                    newtask.buildfreighter.apply_async(args=(world.worldid, task.pk, amount), eta=outcometime)
                    result = outcomes.freighters('Success', amount)

        if "research" in form:
            form = ResearchForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                amount = data['researchamount']
                if amount < 0:
                    result = 'Enter a positive integer.'
                elif displaybuilds[8]:
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
                    world.turnresearched = True
                    world.budget = F('budget') - amount
                    world.duranium = F('duranium') - durcost
                    world.tritanium = F('tritanium') - tritcost
                    world.adamantium = F('adamantium') - adamcost
                    world.save(update_fields=['turnresearched','budget','duranium','tritanium','adamantium'])
                    if world.region == 'D':
                        amount = int(amount*1.25)

                    message = outcomes.researchtext(world, amount)

                    world.millevel = F('millevel') + amount
                    world.save(update_fields=['millevel'])
                    result = outcomes.research('Success', result=message)

        if "moveship" in form:
            form = ShipMoveForm(world, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                amount = data['amount']
                regionfrom = data['regionfrom']
                regionto = data['regionto']
                if shiptype == 0:
                    movecheck = utilities.freightercheck(world, regionfrom, amount)
                    if regionfrom == regionto:
                        result = 'You cannot warp within the same sector!'
                    elif amount < 1:
                        result = 'You must send at least one freighter!'
                    elif movecheck == False:
                        result = 'You do not have the required freighters in that sector!'
                    else:
                        outcometime = v.now() + time.timedelta(hours=2)
                        taskdetails = taskdata.movefreighter(amount, regionfrom, regionto)
                        task = Task(target=world, content=taskdetails, revokable=True, datetime=outcometime)
                        task.save()
                        newtask.movefreighter.apply_async(args=(world.worldid,task.pk,amount,regionfrom,regionto), eta=outcometime)
                        result = 'Your freighters are charging up their warp drives for a jump in 2 hours\' time.'
                elif shiptype == 10:
                    if regionfrom == regionto:
                        result = 'You cannot warp within the same sector!'
                    elif world.flagshiptype == 0:
                        result = 'You do not own a personal ship!'
                    elif world.flagshiplocation != regionfrom:
                        result = 'Your personal ship is not in that sector!'
                    else:
                        outcometime = v.now() + time.timedelta(hours=8)
                        taskdetails = taskdata.movepersonalship(regionfrom, regionto)
                        task = Task(target=world, content=taskdetails, revokable=True, datetime=outcometime)
                        task.save()
                        newtask.movepersonalship.apply_async(args=(world.worldid,task.pk,regionfrom,regionto), eta=outcometime)
                        result = 'Your personal ship is charging up its warp drive for a jump in 8 hours\' time.'
                else:
                    shiplist = [0,0,0,0,0,0,0,0,0]
                    shiplist[shiptype-1] = amount
                    fuelcost = int(0.5 * utilities.warpfuelcost(shiplist) + 0.5)
                    movecheck = utilities.movecheck(world, shiptype, amount, regionfrom)
                    if regionfrom == regionto:
                        result = 'You cannot warp within the same sector!'
                    elif amount < 1:
                        result = 'You must warp at least one ship!'
                    elif movecheck == False:
                        result = 'You do not have the required ships in that sector!'
                    else:
                        outcometime = v.now() + time.timedelta(hours=8)
                        trainingchange = utilities.trainingchangecalc(world, regionfrom, shiptype, amount)
                        taskdetails, shipname = taskdata.moveship(shiptype, amount, regionfrom, regionto)
                        task = Task(target=world, content=taskdetails, revokable=True, datetime=outcometime)
                        task.save()
                        newtask.moveship.apply_async(args=(world.worldid,task.pk,amount,shiptype,
                            shipname,regionfrom,regionto,fuelcost,trainingchange), eta=outcometime)
                        result = 'Your ships are charging up their warp drives for a jump in 8 hours\' time.'

        if "plusmothball" in form:
            form = ShipMothballForm(world.millevel, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                amount = data['amount']
                shiplist = [0,0,0,0,0,0,0,0,0]
                shiplist[shiptype-1] = amount
                fuelcost = int(0.5 * utilities.warpfuelcost(shiplist) + 0.5)
                if 'sendstaging' in world.shipsortprefs:
                    movecheck = utilities.movecheck(world, shiptype, amount, 'S')
                else:
                    movecheck = utilities.movecheck(world, shiptype, amount, world.region)
                if amount < 1:
                    result = 'You must mothball at least one ship!'
                elif movecheck == False:
                    result = 'You do not have that many ships in your home fleet!'
                else:
                    outcometime = v.now() + time.timedelta(hours=8)
                    trainingchange = utilities.trainingchangecalc(world, world.region, shiptype, amount)
                    taskdetails, shipname = taskdata.mothball(shiptype, amount, 'plus')
                    task = Task(target=world, content=taskdetails, revokable=True, datetime=outcometime)
                    task.save()
                    newtask.mothball.apply_async(args=(world.worldid,task.pk,amount,shiptype,
                        shipname,fuelcost,trainingchange,'plus'), eta=outcometime)
                    result = 'Your ships are making preparations to decommission, <br> \
                        and will enter the orbital hangars in 8 hours\' time.'

        if "minusmothball" in form:
            form = ShipMothballForm(world.millevel, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                amount = data['amount']
                shiplist = [0,0,0,0,0,0,0,0,0]
                shiplist[shiptype-1] = amount
                fuelcost = int(0.5 * utilities.warpfuelcost(shiplist) + 0.5)
                movecheck = utilities.movecheck(world, shiptype, amount, 'H')
                if amount < 1:
                    result = 'You must mothball at least one ship!'
                elif movecheck == False:
                    result = 'You do not have that many ships currently mothballed!'
                else:
                    outcometime = v.now() + time.timedelta(hours=8)
                    trainingchange = utilities.trainingchangecalc(world, 'H', shiptype, amount)
                    taskdetails, shipname = taskdata.mothball(shiptype, amount, 'minus')
                    task = Task(target=world, content=taskdetails, revokable=True, datetime=outcometime)
                    task.save()
                    newtask.mothball.apply_async(args=(world.worldid,task.pk,amount,shiptype,
                        shipname,fuelcost,trainingchange,'minus'), eta=outcometime)
                    result = 'Your ships are making preparations to re-enter active service, <br> \
                        and will re-join the home fleet in 8 hours\' time.'

        if "plusstage" in form:
            form = StagingForm(world.millevel, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                amount = data['amount']
                if shiptype == 0:
                    movecheck = utilities.freightercheck(world, world.region, amount)
                    if not utilities.checkno(amount):
                        result = 'You must stage at least one freighter!'
                    elif movecheck == False:
                        result = 'You do not have that many freighters to stage!'
                    else:
                        utilities.freightermove(world, world.region, -amount)
                        utilities.freightermove(world, 'S', amount)
                        result = 'Freighters successfully staged!'
                else:
                    movecheck = utilities.movecheck(world, shiptype, amount, world.region)
                    if not utilities.checkno(amount):
                        result = 'You must stage at least one ship!'
                    elif movecheck == False:
                        result = 'You do not have that many ships to stage!'
                    else:
                        trainingchange = utilities.trainingchangecalc(world, world.region, shiptype, amount)
                        utilities.movecomplete(world,shiptype,-amount,world.region,-trainingchange)
                        utilities.movecomplete(world,shiptype,amount,'S',trainingchange)
                        result = 'Ships successfully staged!'

        if "minusstage" in form:
            form = StagingForm(world.millevel, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['shiptype']
                amount = data['amount']
                if shiptype == 0:
                    movecheck = utilities.freightercheck(world, 'S', amount)
                    if not utilities.checkno(amount):
                        result = 'You must unstage at least one freighter!'
                    elif movecheck == False:
                        result = 'You do not have that many freighters to unstage!'
                    else:
                        utilities.freightermove(world, 'S', -amount)
                        utilities.freightermove(world, world.region, amount)
                        result = 'Freighters successfully unstaged!'
                else:
                    movecheck = utilities.movecheck(world, shiptype, amount, 'S')
                    if not utilities.checkno(amount):
                        result = 'You must unstage at least one ship!'
                    elif movecheck == False:
                        result = 'You do not have that many ships to unstage!'
                    else:
                        trainingchange = utilities.trainingchangecalc(world, 'S', shiptype, amount)
                        utilities.movecomplete(world,shiptype,-amount,'S',-trainingchange)
                        utilities.movecomplete(world,shiptype,amount,world.region,trainingchange)
                        result = 'Ships successfully unstaged!'

        if "plusstageall" in form:
            shiplist = utilities.regionshiplist(world, world.region)
            freighters = utilities.freighterregion(world, world.region)
            if sum(shiplist) == 0 and freighters == 0:
                result = "You have no ships to stage!"
            else:
                for index, value in enumerate(shiplist):
                    trainingchange = utilities.trainingchangecalc(world, world.region, index+1, value)
                    utilities.movecomplete(world,index+1,-value,world.region,-trainingchange)
                    world = World.objects.get(pk=world.pk)
                    utilities.movecomplete(world,index+1,value,'S',trainingchange)
                utilities.freightermove(world, world.region, -freighters)
                utilities.freightermove(world, 'S', freighters)
                result = "All ships successfully staged!"

        if "minusstageall" in form:
            shiplist = utilities.regionshiplist(world, 'S')
            freighters = utilities.freighterregion(world, 'S')
            if sum(shiplist) == 0 and freighters == 0:
                result = "You have no ships to unstage!"
            else:
                for index, value in enumerate(shiplist):
                    trainingchange = utilities.trainingchangecalc(world, 'S', index+1, value)
                    utilities.movecomplete(world,index+1,-value,'S',-trainingchange)
                    world = World.objects.get(pk=world.pk)
                    utilities.movecomplete(world,index+1,value,world.region,trainingchange)
                utilities.freightermove(world, 'S', -freighters)
                utilities.freightermove(world, world.region, freighters)
                result = "All ships successfully unstaged!"

        if "trainfleet" in form:
            if world.budget < trainingcosth:
                result = outcomes.nomoney()
            elif currenth >= maximumh:
                result = outcomes.training('AtMax')
            else:
                utilities.trainingchange(world, world.region, maximumh/10)
                world.budget = F('budget') - trainingcosth
                world.save(update_fields=['budget'])
                result = outcomes.training('Success')

        if "trainstaging" in form:
            if world.budget < trainingcosts:
                result = outcomes.nomoney()
            elif currents >= maximums:
                result = outcomes.training('AtMax')
            else:
                utilities.trainingchange(world, 'S', maximums/10)
                world.budget = F('budget') - trainingcosts
                world.save(update_fields=['budget'])
                result = outcomes.training('Success')

        if "buildshipyard" in form:
            if world.budget < 500:
                result = outcomes.nomoney()
            elif world.duranium < 5:
                result = outcomes.notenoughduranium()
            else:
                world.budget = F('budget') - 500
                world.duranium = F('duranium') - 5
                world.shipyards = F('shipyards') + 1
                world.save(update_fields=['budget','duranium','shipyards'])
                result = outcomes.shipyards('Success')

        if "attackrebels" in form:
            worldpower = utilities.militarypower(world, world.region)
            worldlist = utilities.regionshiplist(world, world.region)
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

                totworldpower = utilities.powerallmodifiers(world, world.region)

                rebelpower = 0
                for region in ['A','B','C','D','S']:
                    rebelpower += utilities.militarypower(world, region) # sum of total fleet power

                deflosses = [0, 0, 0, 0, 0, 0, 0, 0, 0]
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
                    deflosses = utilities.war_result(rebelpower, totworldpower, worldpower, worldlist)
                    utilities.warloss_byregion(world, world.region, deflosses)

                if 30 < outcome <= 100:
                    utilities.rebelschange(world, -5)
                elif 1 <= outcome <= 5:
                    utilities.rebelschange(world, 5)

                utilities.wearinesschange(world, world.region, -2)

                world.save(update_fields=['budget','warpfuel'])

                result = news.rebelresult(outcome, deflosses)

        if "setstagingprefs" in form:
            listprefs = request.POST.getlist('stagingpref')
            check = True
            onlyone = 'You can only select one option in each category!'
            prod = send = receive = 0
            for pref in listprefs:
                if pref not in v.stagingprefs:
                    check = False
                if 'prod' in pref:
                    prod += 1
                if 'send' in pref:
                    send += 1
                if 'receive' in pref:
                    receive += 1
            if len(listprefs) != 3:
                result = 'You must select one option in each category.'
            elif check == False:
                result = 'You have selected an invalid preference!'
            elif prod != 1:
                result = onlyone
            elif send != 1:
                result = onlyone
            elif receive != 1:
                result = onlyone
            else:
                shipprefs = ','.join(listprefs)
                world.shipsortprefs = shipprefs
                world.save(update_fields=['shipsortprefs'])
                result = 'Preferences updated.'

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
                    outcometime = v.now() + time.timedelta(hours=5)
                    world.budget = F('budget') - D(500)
                    world.duranium = F('duranium') - 20
                    world.shipyardsinuse = F('shipyardsinuse') + 5
                    world.flagshipbuild = True
                    world.save(update_fields=['budget','duranium','shipyardsinuse','flagshipbuild'])
                    taskdetails = taskdata.buildpersonalship(shiptype)
                    task = Task(target=world, content=taskdetails, datetime=outcometime)
                    task.save()

                    newtask.buildpersonalship.apply_async(args=(world.worldid, task.pk, shiptype), eta=outcometime)
                    result = outcomes.personalship('Success', shiptype)

        if "scuttleflagship" in form:
            if world.flagshiptype == 0:
                result = 'You do not have a flagship to scuttle!'
            else:
                utilities.flagshipreset(world)
                result = 'You scuttled your flagship.'

    # reload data
    world = World.objects.get(pk=world.pk)

    prefs = world.shipsortprefs
    moveform = ShipMoveForm(world)
    mothballform = ShipMothballForm(world.millevel)
    stagingform = StagingForm(world.millevel)
    researchform = ResearchForm()
    personalshipform = PersonalShipForm()

    buildpref = world.buildpref
    trainingcosth = utilities.trainingcost(world, world.region)
    currenth, maximumh = utilities.trainingstatus(world, world.region)
    trainingstatush = ('No Fleet' if maximumh == 0 else display.training_display(currenth, maximumh))
    trainingcosts = utilities.trainingcost(world, 'S')
    currents, maximums = utilities.trainingstatus(world, 'S')
    trainingstatuss = ('No Fleet' if maximums == 0 else display.training_display(currents, maximums))
    money = world.budget
    yardsfree = world.shipyards - world.shipyardsinuse
    yardsinuse = world.shipyardsinuse
    rumpolicy = (True if world.rumsoddium == 4 else None)
    nopersonalship = (True if world.flagshiptype == 0 or world.flagshipbuild else None)

    return render(request, 'policies_military.html', {'result':result, 'trainingcost':trainingcosth, 'moveform':moveform, 'datafig':datafig,
        'datacor':datacor, 'datalcr':datalcr, 'datades':datades, 'datafri':datafri, 'datahcr':datahcr, 'databcr':databcr, 'databsh':databsh,
        'datadre':datadre, 'money':money, 'displayresearch':displayresearch, 'researchform':researchform, 'costmsg':costmsg, 'shiptext':shiptext,
        'rebelfuelcost':rebelfuelcost, 'indefwar':indefwar, 'mothballform':mothballform, 'stagingform':stagingform, 'prefs':prefs,
        'stagingtrainingcost':trainingcosts, 'yardsfree':yardsfree, 'yardsinuse':yardsinuse, 'buildpref':buildpref, 'displaybuilds':displaybuilds,
        'statush':trainingstatush, 'statuss':trainingstatuss, 'rumpolicy':rumpolicy, 'rumsodmsg':rumsodmsg, 'nopersonalship':nopersonalship,
        'personalshipform': personalshipform})
