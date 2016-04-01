# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import random, decimal

# WaW Imports
from wawmembers.models import *
from wawmembers.forms import *
from wawmembers.decorators import world_required
import wawmembers.newsgenerator as news
import wawmembers.variables as v

'''
All news items and their effects are here.
'''

D = decimal.Decimal

@login_required
@world_required
def world_news(request):

    world = World.objects.get(worldid=request.user.id)
    anlist = ActionNewsItem.objects.filter(target=world)
    message = None
    notask = 'No such news item!'

    if request.method == 'POST':
        form = request.POST
        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('newsitem')
            for i in listitems:
                try:
                    item = NewsItem.objects.get(pk=i)
                except ObjectDoesNotExist:
                    message = notask
                else:
                    if item.target == world:
                        item.delete()

        if "deleteall" in form:   # deletes all news
            NewsItem.objects.filter(target=world).delete()

        ##############
        ### ACTIONNEWS
        ##############

        ##
        ## TYPE 1
        ##
        if (("acceptpeace" in form) or ("declinepeace" in form)) and (anlist.filter(actiontype=1).exists()): # type 1
            taskid = request.POST.get('taskid')
            war = None
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except ObjectDoesNotExist:
                message = notask
            else:
                try:
                    war = actionnewsitem.peacebyatk.all()[0]
                except IndexError:
                    try:
                        war = actionnewsitem.peacebydef.all()[0]
                    except IndexError:
                        message = 'You are not at war with this world!'
            if war != None:
                if "acceptpeace" in form:
                    htmldata = news.peaceaccept(world)
                    if world == war.attacker and war.peaceofferbydef != None:
                        NewsItem.objects.create(target=war.defender, content=htmldata)
                    elif world == war.defender and war.peaceofferbyatk != None:
                        NewsItem.objects.create(target=war.attacker, content=htmldata)

                    war.delete()
                    message = 'You are now at peace.'

                if "declinepeace" in form:
                    htmldata = news.peacedecline(world)
                    if world == war.attacker and war.peaceofferbydef != None:
                        NewsItem.objects.create(target=war.defender, content=htmldata)
                    elif world == war.defender and war.peaceofferbyatk != None:
                        NewsItem.objects.create(target=war.attacker, content=htmldata)

                    actionnewsitem.delete()
                    message = 'The peace offer has been declined.'

        ##
        ## TYPE 2
        ##
        if ("noobmoney" in form) and (anlist.filter(actiontype=2).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    world.budget = F('budget') + D(600)
                    world.save(update_fields=['budget'])
                    message = 'Money! Money falling from the skies!'

        if ("noobqol" in form) and (anlist.filter(actiontype=2).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    utilities.qolchange(world, 40)
                    utilities.contentmentchange(world, 40)
                    message = 'Well, aren\'t you a humanitarian?'

        if ("noobsecurity" in form) and (anlist.filter(actiontype=2).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    utilities.stabilitychange(world, 60)
                    message = 'Your people are used to absolute obedience to your rule.'

        if ("noobmilitary" in form) and (anlist.filter(actiontype=2).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    utilities.movecomplete(world, 1, 10, world.region, 40)
                    world.warpfuelprod = F('warpfuelprod') + 10
                    world.save(update_fields=['warpfuelprod'])
                    message = 'Your warmongering world starts out with extra fighters!'

        ##
        ## TYPE 3
        ##
        if ("fleetresearch" in form) and (anlist.filter(actiontype=3).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    world.millevel = F('millevel') + 1500
                    world.save(update_fields=['millevel'])
                    message = 'You pour intensive effort into bettering your ship technology.'

        if ("fleetshipyard" in form) and (anlist.filter(actiontype=3).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    world.shipyards = F('shipyards') + 1
                    world.save(update_fields=['shipyards'])
                    message = 'You must build ships faster! You construct a shipyard as fast as possible.'

        if ("fleettraining" in form) and (anlist.filter(actiontype=3).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    maximum = utilities.trainingfromlist(utilities.regionshiplist(world, world.region))
                    utilities.trainingchange(world, world.region, maximum/10)
                    message = 'You order a series of war and battle simulations and training improves a great deal.'

        ##
        ## TYPE 4
        ##
        if ("asteroidduranium" in form) and (anlist.filter(actiontype=4).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    actionnewsitem.delete()
                    world.duraniumprod = F('duraniumprod') + 3
                    world.save(update_fields=['duraniumprod'])
                    message = 'You set up a duranium mine on the asteroid.'

        if ("asteroidtritanium" in form) and (anlist.filter(actiontype=4).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.millevel < v.millevel('lcr'):
                        message = 'Your military level is not high enough to refine this material!'
                    else:
                        actionnewsitem.delete()
                        world.tritaniumprod = F('tritaniumprod') + 2
                        world.save(update_fields=['tritaniumprod'])
                        message = 'You set up a tritanium mine on the asteroid.'

        if ("asteroidadamantium" in form) and (anlist.filter(actiontype=4).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.millevel < v.millevel('hcr'):
                        message = 'Your military level is not high enough to refine this material!'
                    else:
                        actionnewsitem.delete()
                        world.adamantiumprod = F('adamantiumprod') + 1
                        world.save(update_fields=['adamantiumprod'])
                        message = 'You set up an adamantium mine on the asteroid.'

        ##
        ## TYPE 5
        ##
        if ("dasteroiddeflect" in form) and (anlist.filter(actiontype=5).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.warpfuel < 50:
                        message = 'You do not have enough warpfuel for this event!'
                    else:
                        actionnewsitem.delete()
                        world.warpfuel = F('warpfuel') - 50
                        world.save(update_fields=['warpfuel'])
                        message = 'You deflect the asteroid harmlessly into space.'

        if ("dasteroidsubcontract" in form) and (anlist.filter(actiontype=5).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.budget < 500:
                        message = 'You do not have enough money for this event!'
                    else:
                        actionnewsitem.delete()
                        world.budget = F('budget') - D(500)
                        world.save(update_fields=['budget'])
                        message = 'You pay a civilian group to deflect the asteroid for you.'

        if ("dasteroidredirect" in form) and (anlist.filter(actiontype=5).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.warpfuel < 20:
                        message = 'You do not have enough warpfuel for this event!'
                    else:
                        actionnewsitem.delete()
                        world.warpfuel = F('warpfuel') - 20
                        utilities.rebelschange(world, -20)
                        utilities.contentmentchange(world, -40)
                        world.save(update_fields=['warpfuel'])
                        message = 'You redirect the asteroid onto an area of the planet you know<br>rebels like to hide in. \
                            Any rebels you may have suffer<br>heavy losses, but the population is horrified at you.'

        ##
        ## TYPE 6
        ##
        if ("radmiralignore" in form) and (anlist.filter(actiontype=6).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if random.randint(1,3) == 1:
                        utilities.rebelschange(world, 5)
                        utilities.stabilitychange(world, -20)
                        message = 'It seems you were wrong! Stability drops as <br> the admiral musters rebels to your rule.'
                    else:
                        world.budget = F('budget') + D(500)
                        world.save(update_fields=['budget'])
                        message = 'You were right. The people take your side and you eventually <br> \
                            confiscate the admiral\'s property, sending him off-world.'

                    actionnewsitem.delete()

        if ("radmiralbribe" in form) and (anlist.filter(actiontype=6).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.budget < 250:
                        message = 'You do not have enough money for this event!'
                    elif random.randint(1,10) == 1:
                        world.budget = F('budget') - D(250)
                        utilities.stabilitychange(world, 10)
                        world.save(update_fields=['budget'])
                        message = 'The admiral accepts your payoffs and retires, extolling your <br> \
                            virtues in his retirement speech broadcast around the world.'
                    else:
                        world.budget = F('budget') - D(250)
                        utilities.rebelschange(world, 5)
                        utilities.stabilitychange(world, -20)
                        world.save(update_fields=['budget'])
                        message = 'The admiral takes your money and uses it to raise rebels against your rule!'

                    actionnewsitem.delete()

        if ("radmiralspy" in form) and (anlist.filter(actiontype=6).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if not Spy.objects.filter(owner=world, location=world).exists():
                        message = 'You do not have a spy at home!'
                    elif random.randint(1,4) == 1:
                        utilities.rebelschange(world, 10)
                        utilities.stabilitychange(world, -10)
                        message = 'The admiral survives his \'accident\' and the people, <br> \
                            shocked at your methods, rise up against you.'
                    else:
                        world.budget = F('budget') + D(500)
                        world.save(update_fields=['budget'])
                        message = 'Your spy succeeds in his mission, and the people soon forget what <br> \
                            all the fuss was about. You confiscate the dead admiral\'s property.'

                    actionnewsitem.delete()

        ##
        ## TYPE 7
        ##
        if ("traidersattack" in form) and (anlist.filter(actiontype=7).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    rebelpower = 50
                    worldpower = utilities.militarypower(world, world.region)
                    totworldpower = utilities.powerallmodifiers(world, world.region)
                    worldlist = utilities.regionshiplist(world, world.region)
                    deflosses = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                    deflosses = utilities.war_result(rebelpower, totworldpower, worldpower, worldlist)
                    utilities.warloss_byregion(world, world.region, deflosses)
                    losses = news.losses(deflosses)
                    message = 'You defeated the raiders - the fleet lost %s in the engagement.' % losses
                    actionnewsitem.delete()

        if ("traidersbribe" in form) and (anlist.filter(actiontype=7).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    if world.budget < 500:
                        message = 'You do not have enough money for this event!'
                    elif random.randint(1,10) == 1:
                        world.budget = F('budget') - D(500)
                        utilities.rebelschange(world, 5)
                        world.save(update_fields=['budget'])
                        message = 'The raiders take your money and use it to better equip their <br> \
                            ships and mount more organised attacks in your system!'
                        actionnewsitem.delete()
                    else:
                        world.budget = F('budget') - D(500)
                        world.save(update_fields=['budget'])
                        message = 'The raiders use the payoff to leave for another system.'
                        actionnewsitem.delete()

        if ("traidersignore" in form) and (anlist.filter(actiontype=7).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    utilities.rebelschange(world, 10)
                    message = 'The raiders use the lack of response to organise themselves <br> \
                        and recruit more scum for a greater presence in your system.'
                    actionnewsitem.delete()

        ##
        ## TYPE 8
        ##
        if ("durasteroidmine" in form) and (anlist.filter(actiontype=8).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    duranium = random.randint(70,100)
                    utilities.qolchange(world, -10)
                    world.duranium = F('duranium') + duranium
                    world.save(update_fields=['duranium'])
                    message = 'You managed to extract %s duranium from the asteroid.' % duranium
                    actionnewsitem.delete()

        ##
        ## TYPE 9
        ##
        if ("fuelexplodeaccept" in form) and (anlist.filter(actiontype=9).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    message = 'You send form letters of commiseration to the worker\'s families.'
                    actionnewsitem.delete()

        ##
        ## TYPE 10
        ##
        if ("xenuaccept" in form) and (anlist.filter(actiontype=10).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    utilities.qolchange(world, -10)
                    world.gdp = F('gdp') + 100
                    world.save(update_fields=['gdp'])
                    message = 'Quality of life goes down somewhat from the tortured spirits hassling <br> your population, \
                        but you gain 100 GDP from all the businesses <br> that have popped up to rid them through \'auditing sessions\'.'
                    actionnewsitem.delete()

        if ("xenurefuse" in form) and (anlist.filter(actiontype=10).exists()):
            taskid = request.POST.get('taskid')
            try:
                actionnewsitem = ActionNewsItem.objects.get(pk=taskid)
            except:
                message = 'No such task!'
            else:
                if actionnewsitem.target == world:
                    message = 'The angry despot attempts to detonate a primitive Old Earth bomb <br> on your capital city \
                        but you effortlessly warp it out of existence.<br> Humiliated, he leaves.'
                    actionnewsitem.delete()

    newslist = list(NewsItem.objects.filter(target=world).order_by('-datetime')) # reverse chrono order
    actionnewslist = list(ActionNewsItem.objects.filter(target=world).order_by('-datetime'))

    if len(newslist) == 0:   # Displays 'no news'
        newslist = None
    if len(actionnewslist) == 0:
        actionnewslist = None

    world = World.objects.get(pk=world.pk)
    world.save()

    NewsItem.objects.filter(target=world).update(seen=True)
    ActionNewsItem.objects.filter(target=world).update(seen=True)

    return render(request, 'world_news.html', {'news': newslist, 'actionnews': actionnewslist, 'message':message})
