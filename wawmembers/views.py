# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import F, Q
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.template.defaultfilters import slugify

# Python Imports
from collections import OrderedDict
import random, decimal
import datetime as time
import json

# WaW Imports
from wawmembers.models import *
from wawmembers.forms import *
from wawmembers.decorators import world_required
from wawmembers.loggers import tradelogger
import wawmembers.tasks as newtask
import wawmembers.display as display
import wawmembers.outcomes_policies as outcomes
import wawmembers.newsgenerator as news
import wawmembers.taskgenerator as taskdata
import wawmembers.utilities as utilities
import wawmembers.variables as v
import wawmembers.turnupdates as turnupdates
from wawmembers.interactions import stats_ind

'''
The main file. Most page functions are carried out here.
'''

D = decimal.Decimal


def index(request):
    'Front page.'
    donators = cache.get('donators') # no need to
    if not donators:
        donators = list(preferences.objects.filter(donor=True).exclude(world__pk=1))
        cache.set('donators', donators, 60 * 60 * 24)
    return render(request, 'index.html', {'donators': donators})


@login_required
@world_required
def main(request, message=None):
    'Main page: user\'s world.'
    world = request.user.world
    researchlevels = GlobalData.objects.get(pk=1)
    haswars = offlist = deflist = None
    warprotection = abovegdpprotection = brokenwarprotect = None
    upkeep = 0
    for entry in v.upkeep:
        upkeep += world.__dict__[entry] * v.upkeep[entry]
        if world.sector == 'cleon':
            upkeep *= 0.8 #total upkeep
    upkeep = round(upkeep)
    ip = request.META.get('REMOTE_ADDR')
    world.lastloggedinip = ip
    world.lastloggedintime = v.now()
    world.save(update_fields=['lastloggedinip', 'lastloggedintime'])

    if world.warattacker.count() > 0 or world.wardefender.count() > 0:
        haswars = True
        offlist = [war.defender for war in world.warattacker.all()]
        deflist = [war.attacker for war in world.wardefender.all()]

    displaybuilds = [False for i in range(9)]

    rindex = v.tiers.index(world.techlevel) + 1
    if world.techlevel != v.tiers[len(v.tiers) - 1]: #max tier
        progress = world.millevel/float(researchlevels.tiers()[v.tiers[rindex]]) #lol
    else:
        progress = None

    for index, value in enumerate(displaybuilds[:rindex-1]):
        displaybuilds[index] = True

    if progress is not None:
        progress = int(100*progress/5.0)*5
    milinfo = utilities.mildisplaylist(world)
    mildisplay = display.fleet_display(milinfo[0], milinfo[1])
    sparefreighters = world.freighters - world.freightersinuse

    tooltips = utilities.tooltipdisplay(world)
    #shiploc = display.region_display(world.flagshiplocation)

    if world.warprotection > v.now():
        timediff = world.warprotection - v.now()
        h,m,s = utilities.timedeltadivide(timediff)
        if timediff.days > 0:
            warprotection = 'You are in war protection for another %s days, %s:%s:%s.' % (timediff.days,h,m,s)
        else:
            warprotection = 'You are in war protection for another %s:%s:%s.' % (h,m,s)
    if world.abovegdpprotection > v.now():
        timediff = world.abovegdpprotection - v.now()
        h,m,s = utilities.timedeltadivide(timediff)
        if timediff.days > 0:
            abovegdpprotection = 'You can be attacked by higher GDP worlds for another %s days, %s:%s:%s.' % (timediff.days,h,m,s)
        else:
            abovegdpprotection = 'You can be attacked by higher GDP worlds for another %s:%s:%s.' % (h,m,s)
    if world.brokenwarprotect > v.now():
        timediff = world.brokenwarprotect - v.now()
        h,m,s = utilities.timedeltadivide(timediff)
        brokenwarprotect = 'You are not able to gain war protection for another %s:%s:%s.' % (h,m,s)

    return render(request, 'main.html', {'world': world, 'alliance': world.alliance, 'displaybuilds':displaybuilds,
        'mildisplay': mildisplay, 'haswars':haswars, 'sparefreighters': sparefreighters, 'tooltips': tooltips,
        'offlist':offlist, 'deflist':deflist, 'upkeep': upkeep, 'progress':progress, 'warprotection':warprotection, 'message':message,
        'abovegdpprotection':abovegdpprotection, 'brokenwarprotect':brokenwarprotect})

#wrapper for world page view to enable custom urls
def world_page(request, url):
    try:
        target = World.objects.get(pk=url)
    except:
        try:
            target = donorurl.objects.get(url=url)
        except: #captured url is neither a primary key or custom url
            return render(request, 'notfound.html', {'item': 'world'}) # instead of 404
        else:
            return stats_ind(request, target.owner.world.pk)
    return stats_ind(request, url)


@login_required
@world_required
def fleet_management(request):
    world = request.user.world
    if world.tempmsg:
        result = world.tempmsg
        World.objects.filter(pk=world.pk).update(tempmsg="")
    else:
        result = ""
    if request.method == "POST":
        if 'merge' in request.POST:
            try:
                mergee = world.fleets.all().get(pk=request.POST['merge'])
            except:
                result = "stop using inspect element asshole"
            else:
                form = mergeform(world, mergee, request.POST)
                if form.is_valid():
                    utilities.atomic_fleet(form.cleaned_data['fleetchoice'].pk, 'merge', mergee.pk)
                    if mergee.sector != 'hangar':
                        mergee.delete()
                    result = "%s has successfully been merged into %s!" % (mergee.name, form.cleaned_data['fleetchoice'])
                else:
                    result = "Invalid fleet choice"

        elif 'recall' in request.POST:
            try:
                recallee = world.fleets.all().get(pk=request.POST['recall'])
            except:
                result = "stop using inspect element asshole"
            else:
                form = sectorchoice(request.POST)
                if form.is_valid():
                    fuelstatus = recallee.enoughfuel()
                    if fuelstatus[1] != 'warpfuel': 
                        #set taskdata and subtract fuelcost from host world
                        #then warp the fleet and add newsitem to recalled world
                        if form.cleaned_data['choice'] == recallee.sector:
                            delay = 4
                        else:
                            delay = 8
                        outcometime = v.now() + time.timedelta(hours=delay)
                        action = {'warpfuel': {'action': 'subtract', 'amount': recallee.fuelcost()}}
                        utilities.atomic_world(recallee.controller.pk, action)
                        action = {'set': {'controller': world, 'sector': 'warping'}}
                        utilities.atomic_fleet(recallee.pk, action)
                        taskdetails = taskdata.recallfleet(recallee.name, 
                            recallee.controller.name, form.cleaned_data['choice'])
                        task = Task.objects.create(target=world, 
                            content=taskdetails, datetime=outcometime)
                        newtask.fleet_warp.apply_async(args=(recallee.pk, 
                            form.cleaned_data['choice'], task.pk), eta=outcometime)
                        result = "Fleet %s bugs out and is headed home" % recallee.name
                    else:
                        result = "%s doesn't have enough fuel to send our boys home!" % recallee.controller.name
                else:
                    result = "can't inspect element your way to cheats bruv"

        elif 'sendback' in request.POST:
            try:
                sendbackee = world.controlled_fleets.all().get(pk=request.POST['sendback'])
            except:
                result = "stop using inspect element m8"
            else:
                form = sectorchoice(request.POST)
                if form.is_valid():
                    fuelstatus = sendbackee.enoughfuel()
                    if fuelstatus[1] != 'warpfuel': #set taskdata and subtract fuelcost from host world
                        #then warp the fleet and add newsitem to recalled world
                        if form.cleaned_data['choice'] == sendbackee.sector:
                            delay = 4
                        else:
                            delay = 8
                        outcometime = v.now() + time.timedelta(hours=delay)
                        action = {'warpfuel': {'action': 'subtract', 'amount': sendbackee.fuelcost()}}
                        utilities.atomic_world(world.pk, action)
                        action = {'set': {'controller': sendbackee.world, 'sector': 'warping'}}
                        utilities.atomic_fleet(sendbackee.pk, action)
                        taskdetails = taskdata.sendbackfleet(sendbackee.name, 
                            world.name, form.cleaned_data['choice'])
                        task = Task.objects.create(target=sendbackee.world, 
                            content=taskdetails, datetime=outcometime)
                        newtask.fleet_warp.apply_async(args=(sendbackee.pk, 
                            form.cleaned_data['choice'], task.pk), eta=outcometime)
                        result = "Fleet %s bugs out and is headed home" % sendbackee.name
                    else:
                        result = "We don't have enough fuel to send them home!"
                else:
                    result = "can't inspect element your way to cheats bruv"

        elif 'changename' in request.POST:
            form = fleetnamechangeform(request.POST)
            if form.is_valid(): #simple namechange
                try: #should be no need to check for race conditions
                    tgt = world.fleets.all().get(name=request.POST['changename'])
                except:
                    result = "Can't change the name of a fleet you don't own"
                else:
                    tgt.name = form.cleaned_data['name']
                    tgt.save(update_fields=['name'])
                    result = "%s has been renamed" % request.POST['changename']
            else:
                result = "Invalid name"

        elif 'newfleet' in request.POST:
            sectorform = sectorchoice(request.POST)
            nameform = fleetnamechangeform(request.POST)
            if nameform.is_valid() and sectorform.is_valid():
                fleet.objects.create(world=world, controller=world, 
                    sector=sectorform.cleaned_data['choice'],
                    name=nameform.cleaned_data['name'])
                result = "%s is ready and has been positioned in %s!" % (nameform.cleaned_data['name'], sectorform.cleaned_data['choice'])
            else:
                if not nameform.is_valid():
                    result = "Name for new fleet is too long!"
                else:
                    result = "Incorrect sector chosen, inspecting element will not yield you anything"

        elif 'delete' in request.POST:
            eligible_fleets = world.fleets.all().filter(controller=world).exclude(sector='warping')
            try:
                Fleet = eligible_fleets.get(pk=request.POST['delete'])
            except:
                result = "This fleet cannot be decomissioned!"
            else:
                if Fleet.empty():
                    result = "%s has been retired from active service!" % Fleet.name
                    Fleet.delete()
                else:
                    result = "This fleet cannot be decomissioned!"

    fleetlist = fleet.objects.filter(Q(world=world)|Q(controller=world)).order_by('sector')
    fleetquery = fleetlist
    len(fleetlist) #evaluate and cache all fleets to avoid multiple database hits
    owned = display.fleetmanagementdisplay(fleetlist.filter(world=world, controller=world), world)
    outstanding = display.fleetmanagementdisplay(fleetlist.exclude(controller=world), world)
    borrowed = display.fleetmanagementdisplay(fleetlist.exclude(world=world), world)
    fleetlist = [
    {'fleets': owned, 'fleetype': 'Owned',
    'owned': True, 'count': len(owned)}, 
    {'fleets': borrowed, 'fleetype': 'Borrowed', 'borrowed': True,
    'owned': False, 'count': len(borrowed)},
    {'fleets': outstanding, 'fleetype': 'Outstanding', 'outstanding': True,
    'owned': True, 'count': len(outstanding)}]
    for entry in fleetlist:
        for fleetobject in entry['fleets']: #WE HAVE TO GO DEEPER
            obj = fleetquery.get(pk=fleetobject['pk'])
            fleetobject.update({'sector': obj.sector, 'empty': obj.empty()})
            if fleetobject['name'] == 'Hangar': #can't change hangars
                fleetobject.update({'nameform': {'name': fleetobject['name']}})
            else:
                fleetobject.update({'nameform': fleetnamechangeform(initial={'name': fleetobject['name']})})
            if obj.world == world and obj.controller == world:
                fleetobject.update({'mergeform': mergeform(world, obj)})

    context = {
        'datablob': fleetlist, 
        'sectorchoiceform': sectorchoice(),
        'result': result,
        'nameform': fleetnamechangeform()}
    return render(request, 'fleet.html', context)

@login_required
@world_required
def fleet_logs(request):
    pass


@login_required
@world_required
def exchange_ships(request):
    context = {}
    world = request.user.world
    if request.method == "POST":
        if 'move' in request.POST:
            fleet1 = world.fleets.all().filter(controller=world).get(pk=request.POST['move'])
            form = mergeform(world, fleet1, request.POST)
            if form.is_valid():
                fleet2 = form.cleaned_data['fleetchoice']
                init = {}
                totals = []
                h1 = utilities.display.highestship(fleet1)
                h2 = utilities.display.highestship(fleet2)
                highest = (h1 if v.shipindices.index(h1) > v.shipindices.index(h2) else h2)
                for ship in v.shipindices:
                    init.update({
                        '%s %s' % (fleet1.pk, ship): fleet1.__dict__[ship],
                        '%s %s' % (fleet2.pk, ship): fleet2.__dict__[ship],
                    })
                    if v.shipindices.index(highest) >= v.shipindices.index(ship):
                        totals.append(fleet1.__dict__[ship] + fleet2.__dict__[ship])

                context.update({
                    'form': Shipexchangeform(fleet1, fleet2, initial=init),
                    'fleet1': {'render': display.fleetexchangedisplay(fleet1, highest), 'name': fleet1.name, 'pk': fleet1.pk},
                    'fleet2': {'render': display.fleetexchangedisplay(fleet2, highest), 'name': fleet2.name, 'pk': fleet2.pk},
                    'totals': totals,
                    })
            else:
                World.objects.filter(pk=world.pk).update(tempmsg="Invalid fleet selected")
                return redirect('fleet_management')
        elif 'set' in request.POST:
            try: #only using eligible fleets
                fleets = world.fleets.all().filter(controller=world).exclude(sector="warping")
                fleet1 = fleets.get(pk=request.POST['fleet1'])
                fleet2 = fleets.get(pk=request.POST['fleet2'])
            except:
                World.objects.filter(pk=world.pk).update(tempmsg="Forging POST data is naughty")
                return redirect('fleet_management')
            form = Shipexchangeform(fleet1, fleet2, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                fleet1_ratio = fleet1.ratio()
                fleet2_ratio = fleet2.ratio()
                h1 = utilities.display.highestship(fleet1)
                h2 = utilities.display.highestship(fleet2)
                highest = (h1 if v.shipindices.index(h1) > v.shipindices.index(h2) else h2)
                utilities.exchange_set(fleet1, fleet2_ratio, data, highest)
                utilities.exchange_set(fleet2, fleet1_ratio, data, highest)
                fleet1.save()
                fleet2.save()
                msg = "Ships successfully exchanged between %s and %s!" % (fleet1.name, fleet2.name)
                World.objects.filter(pk=world.pk).update(tempmsg=msg)
                return redirect('fleet_management')
            else:
                World.objects.filter(pk=world.pk).update(tempmsg="Too many ships entered")
                return exchange_ships(request)

    else:
        return redirect('fleet_management')
    return render(request, 'fleetexchange.html', context)


@login_required
@world_required
def spies(request):
    world = request.user.world
    spieslist = list(Spy.objects.filter(owner=world))
    return render(request, 'spies.html', {'spieslist': spieslist})


@login_required
@world_required
def warlogs(request):
    world = request.user.world

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('Warlogitems')
            for i in listitems:
                try:
                    item = Warlog.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.owner == world:
                        item.delete()

        if "deleteall" in form:   # deletes all news
            Warlog.objects.filter(owner=world).delete()

        if "deletebyworld" in form:
            pk = form["target"]
            try:
                target = World.objects.get(pk=pk)
            except ObjectDoesNotExist:
                pass
            else:
                Warlog.objects.filter(owner=world, target=target).delete()

    loglist = list(Warlog.objects.all().filter(owner=world).order_by('-datetime'))

    deleteform = DeleteByTargetForm(world, 'war')

    return render(request, 'warlogs.html', {'world':world,'loglist': loglist, 'deleteform':deleteform})


@login_required
@world_required
def reslogs(request):
    world = request.user.world
    context = {'world': world}
    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('reslogitems')
            deleted = 0
            for i in listitems:
                try:
                    item = ResourceLog.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.owner == world:
                        item.delete()
                        deleted += 1
            if deleted > 0:
                entry = ('entries' if deleted > 1 else 'entry')
                context.update({'message': '%s log %s deleted' % (deleted, entry)})

        if "deleteall" in form:   # deletes all news
            ResourceLog.objects.filter(owner=world).delete()
            context.update({'message': 'All log entries deleted'})

        if "deletebyworld" in form:
            pk = form["target"]
            try:
                target = World.objects.get(pk=pk)
                count = ResourceLog.objects.filter(owner=world, target=target).count()
            except ObjectDoesNotExist:
                pass
            else:
                ResourceLog.objects.filter(owner=world, target=target).delete()
                deleted = count - ResourceLog.objects.filter(owner=world, target=target).count()
                entry = ('entries' if deleted > 1 else 'entry')
                context.update({'message': '%s log %s deleted' % (deleted, entry)})

    logs = ResourceLog.objects.prefetch_related('resources').filter(owner=world).order_by('-datetime')
    loglist = []
    for log in logs:
        loglist.append({'log': log})
    logdisplay = []
    for log in loglist:
        logs = log['log'].resources.all().order_by('pk')
        resources = []
        for log in logs:
            resources.append([log.resource, log.amount])
        logdisplay.append(utilities.resource_text(resources))
    for log, text in zip(loglist, logdisplay):
        log.update({'text': text})
    deleteform = DeleteByTargetForm(world, 'res')
    context.update({
        'loglist': loglist,
        'deleteform':deleteform,
        })

    return render(request, 'reslogs.html', context)


@login_required
def new_world(request):
    'New world page, only if the user has not already got a world.'

    message = None
    if World.objects.filter(user=request.user).exists():
        return redirect('main')
    else:
        if request.method == 'POST':
            form = NewWorldForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                worldname = data['worldname']
                regionin = data['region']
                econsysin = data['econsystem']
                polsysin = data['polsystem']
                ip = request.META.get('REMOTE_ADDR')
                try:
                    World.objects.get(name=worldname)
                except:
                    pass
                else:
                    message = "That world name is already in use!"
                    return render(request, 'newworld.html', {'form': form,'message':message,'regiondata':v.regiondata,'econdata':v.econdata,'poldata':v.poldata})
                newnation = World.objects.create(user=request.user, gdp=1000, creationip=ip, name=worldname, 
                    sector=regionin, econsystem=econsysin, polsystem=polsysin, freighters=3)
                preferences.objects.create(world=newnation)
                if newnation.user.username in v.donorlist:
                    newnation.preferences.donor = True
                    donorurl.objects.create(owner=newnation.preferences)
                    newnation.save()
                tgt = fleet.objects.create(world=newnation, controller=newnation, name="%s fleet" % newnation.sector, freighters=2, fighters=10, sector=newnation.sector)
                fleet.objects.create(world=newnation, controller=newnation, sector="hangar", name="Hangar")
                newnation.preferences.recievefleet = tgt
                newnation.preferences.buildfleet = tgt
                newnation.preferences.save()
                htmldata = news.newbevent(worldname)
                ActionNewsItem.objects.create(target=newnation, content=htmldata, actiontype=2)
                admin = World.objects.get(pk=1)
                Comm.objects.create(target=newnation, sender=admin, content=v.introcomm)
                return redirect('main')
        else:
            form = NewWorldForm()

    return render(request, 'newworld.html', {'form': form,'message':message,'regiondata':v.regiondata,'econdata':v.econdata,'poldata':v.poldata})


@login_required
@world_required
def settings(request):
    'Users change settings here.'
    world = request.user.world
    message = None
    invalid = 'Invalid preference selected.'

    if request.method == 'POST':
        form = request.POST

        if 'donorurl' in form and world.preferences.donor:
            form = donorurlform(request.POST)
            if form.is_valid():
                try:
                    int(form.cleaned_data['url'])
                except:
                    url = slugify(form.cleaned_data['url'])
                    try:
                        donorurl.objects.get(url=url)
                    except:
                        #good to go
                        world.preferences.donorurl.url = url
                        world.preferences.donorurl.save()
                        message = "URL has been set"
            if message != "URL has been set":
                message = "Invalid URL"

        if "editdesc" in form:
            desc = form['description']
            limit = (500 if world.preferences.donor else 300)
            if len(desc) > limit:
                message = 'The description you entered is too long.'
            elif '<' in desc or '>' in desc:
                message = 'The description contains invalid characters!'
            else:
                world.world_desc = desc
                world.save(update_fields=['world_desc'])
                message = 'Description changed.'

        if "selectsort" in form:
            form = CommDisplayForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pref = data['sortby']
                if pref not in v.commprefs:
                    message = invalid
                else:
                    world.commpref = pref
                    world.save(update_fields=['commpref'])
                    message = 'Comm display preference changed.'

        if "selectpolicy" in form:
            form = PolicyChoiceForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pref = data['policychoice']
                if pref not in v.policyprefs:
                    message = invalid
                else:
                    world.policypref = pref
                    world.save(update_fields=['policypref'])
                    message = 'Policy link preference changed.'

        if "selectship" in form:
            form = ShipChoiceForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pref = data['buildchoice']
                if pref not in v.buildprefs:
                    message = invalid
                else:
                    world.buildpref = pref
                    world.save(update_fields=['buildpref'])
                    message = 'Ship build preference changed.'

        if "selectflagpref" in form:
            form = FlagDisplayForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pref = data['flagpref']
                if pref not in v.commprefs:
                    message = 'Invalid preference selected.'
                else:
                    world.flagpref = pref
                    world.save(update_fields=['flagpref'])
                    message = 'Flag display preference changed.'

        if "selectworldno" in form:
            pref = form['worlddisplayno']
            if not utilities.checkno(pref):
                message = 'Enter a positive number.'
            else:
                world.worlddisplayno = pref
                world.save(update_fields=['worlddisplayno'])
                message = 'World list preference changed.'

        if "setworldprefs" in form:
            listprefs = request.POST.getlist('worldpref')
            worldprefs = ','.join(listprefs)
            world.statsopenprefs = worldprefs
            world.save(update_fields=['statsopenprefs'])
            message = 'World display preferences updated.'

        if "selectflag" in form:
            form = FlagForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                flagid = data['flag']
                if 'fl' not in flagid:
                    message = 'Invalid flag selected.'
                else:
                    world.preferences.flag = flagid
                    world.preferences.save(update_fields=['flag'])
                    message = 'Flag changed.'

        if "selectps" in form:
            form = PersonalShipPicForm(world.flagshiptype, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                picid = data['pspic']
                if (world.flagshiptype == 1 and 'pf' not in picid) \
                  or (world.flagshiptype == 2 and 'my' not in picid) \
                  or (world.flagshiptype == 3 and 'cs' not in picid):
                    message = 'Invalid picture selected.'
                else:
                    world.flagshippicture = picid
                    world.save(update_fields=['flagshippicture'])
                    message = 'Personal ship picture changed.'

        if "selectavatar" in form:
            form = AvatarForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                avatarid = data['avatar']
                if 'av' not in avatarid:
                    message = 'Invalid avatar selected.'
                else:
                    world.preferences.avatar = avatarid
                    world.preferences.save(update_fields=['avatar'])
                message = 'Avatar changed.'

        if "selectbackground" in form:
            form = BackgroundForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                pref = data['background']
                world.backgroundpref = pref
                world.save(update_fields=['backgroundpref'])
                message = 'Background changed.'

        if "setflagshipname" in form:
            name = form['flagshipname']
            if len(name) > 30:
                message = 'The name you entered is too long.'
            else:
                world.flagshipname = name
                world.save(update_fields=['flagshipname'])
                message = 'Flagship name changed.'

        if world.preferences.donor:
            if "setcustomflag" in form:
                customflag = form['customflag']
                world.preferences.donatorflag = customflag
                world.preferences.save(update_fields=['donatorflag'])
                message = 'Flag changed.'

            if "setcustomavatar" in form:
                customavatar = form['customavatar']
                world.preferences.donatoravatar = customavatar
                world.preferences.save(update_fields=['donatoravatar'])
                message = 'Avatar changed.'

            if "setcustomanthem" in form:
                customanthem = form['customanthem']
                world.preferences.donatoranthem = customanthem
                world.preferences.save(update_fields=['donatoranthem'])
                message = 'Anthem changed.'

            if "setcustomps" in form:
                custompic = form['customps']
                world.preferences.donatorflagship = custompic
                world.preferences.save(update_fields=['donatorflagship'])
                message = 'Personal ship picture changed.'

            if "setcustomdescriptor" in form:
                customdescriptor = form['customdescriptor']
                if len(customdescriptor) > 100:
                    message = 'Your custom description is too long! Max 100 characters.'
                else:
                    world.world_descriptor = customdescriptor
                    world.save(update_fields=['world_descriptor'])
                    message = 'Descriptor changed.'

            if "setcustomtitle" in form:
                customtitle = form['customtitle']
                if len(customtitle) > 100:
                    message = 'Your custom title is too long! Max 100 characters.'
                else:
                    world.leadertitle = customtitle
                    world.save(update_fields=['leadertitle'])
                    message = 'Leader title changed.'


    flagform = FlagForm(initial={'flag':world.preferences.flag})
    avatarform = AvatarForm(initial={'avatar':world.preferences.avatar})
    commform = CommDisplayForm(initial={'sortby':world.commpref})
    bgform = BackgroundForm(initial={'background':world.backgroundpref})
    policyform = PolicyChoiceForm(initial={'policychoice':world.policypref})    
    flagdisplayform = FlagDisplayForm(initial={'flagpref':world.flagpref})
    psform = PersonalShipPicForm(world.flagshiptype, initial={'pspic':world.flagshippicture})
    passchangeform = passchange()
    if world.preferences.donor:
        donorurl = donorurlform(initial={'url': world.preferences.donorurl.url})
    else:
        donorurl = donorurlform()
    world = World.objects.get(user=request.user)
    return render(request, 'settings.html', {'world': world, 'message': message,'flagform':flagform, 'avatarform':avatarform, 'commform':commform,
        'bgform':bgform, 'passchangeform': passchangeform, 'donorurlform': donorurl, 'policyform':policyform, 'flagdisplayform':flagdisplayform, 'psform':psform,'test':str(world.backgroundpref)})


# world_news is in news.py


def galacticnews(request):
    'Galactic news - lottery, wars, announcements, stats.'

    message = None
    try:
        world = World.objects.get(user=request.user)
    except:
        displayform = None
        count = 0
    else:
        displayform = True
        count = LotteryTicket.objects.filter(owner=world).count()

        if request.method == 'POST':
            form = request.POST

            if "sendannouncement" in form:
                data = form['announcement']
                if world.budget < 100:
                    message = outcomes.nomoney()
                elif len(data) > 500:
                    message = 'Maximum 500 characters!'
                elif len(data) < 5:
                    message = 'Minimum 5 characters!'
                elif Announcement.objects.filter(sender=world).count() == 10:
                    message = 'You cannot make more than 10 announcements at a time.'
                else:
                    if data in [ann.content for ann in Announcement.objects.all()]:
                        message = 'You cannot repeat an announcement.'
                    else:
                        world.budget = F('budget') - 100
                        world.save(update_fields=['budget'])
                        announcement = Announcement(sender=world, content=data)
                        announcement.save()
                        message = 'Announcement made.'

            if "buyticket" in form:
                amount = form['amount']
                if not utilities.checkno(amount):
                    message = "Enter a positive integer."
                elif int(amount) > 10000:
                    message = "You can only buy 10,000 tickets at a time."
                elif world.budget < 100*int(amount):
                    message = outcomes.nomoney()
                else:
                    amount = int(amount)
                    world.budget = F('budget') - 100*amount
                    world.save(update_fields=['budget'])
                    LotteryTicket.objects.bulk_create([LotteryTicket(owner=world) for i in xrange(amount)])
                    count = LotteryTicket.objects.filter(owner=world).count()

    wars = list(War.objects.all().order_by('-starttime'))
    announcements = list(Announcement.objects.all().order_by('-datetime'))
    rsowners = list(World.objects.filter(rumsoddium__gte=1))

    if len(wars) == 0:
        wars = None
    if len(announcements) == 0:
        announcements = None

    jackpot = LotteryTicket.objects.count()*75 + 200
    days = abs(time.datetime.today().weekday()-6)
    if days == 0:
        timedelta = v.now().replace(hour=23, minute=59, second=0) - v.now()
        h,m,s = utilities.timedeltadivide(timedelta)
        if h == 0:
            timeremaining = "%s %s" % (int(m)+1, utilities.plural('minute', m))
        else:
            timeremaining = "%s %s, %s %s" % (h, utilities.plural('hour', h), int(m)+1, utilities.plural('minute', m))
    else:
        timeremaining = "%s %s" % (days, utilities.plural('day', days))
    counttext = ("You have no tickets." if count == 0 else "You have %s %s." % (count, utilities.plural('ticket', count)))
    stats = cache.get('statistics')
    if not stats:
        totA = World.objects.filter(sector='amyntas').count()
        totB = World.objects.filter(sector='bion').count()
        totC = World.objects.filter(sector='cleon').count()
        totD = World.objects.filter(sector='draco').count()
        totworlds = totA + totB + totC + totD
        totGDP = World.objects.aggregate(Sum('gdp'))['gdp__sum']
        totbudget = World.objects.aggregate(Sum('budget'))['budget__sum']
        totgrowth = World.objects.aggregate(Sum('growth'))['growth__sum']
        totfuel = World.objects.aggregate(Sum('warpfuel'))['warpfuel__sum']
        totdur = World.objects.aggregate(Sum('duranium'))['duranium__sum']
        tottrit = World.objects.aggregate(Sum('tritanium'))['tritanium__sum']
        totadam = World.objects.aggregate(Sum('adamantium'))['adamantium__sum']
        totfuelprod = World.objects.aggregate(Sum('warpfuelprod'))['warpfuelprod__sum']
        totdurprod = World.objects.aggregate(Sum('duraniumprod'))['duraniumprod__sum']
        tottritprod = World.objects.aggregate(Sum('tritaniumprod'))['tritaniumprod__sum']
        totadamprod = World.objects.aggregate(Sum('adamantiumprod'))['adamantiumprod__sum']
        totfreighters = World.objects.aggregate(Sum('freighters'))['freighters__sum']
        totfreighters += fleet.objects.aggregate(Sum('freighters'))['freighters__sum']
        totshipyards = World.objects.aggregate(Sum('shipyards'))['shipyards__sum']
        totfig = fleet.objects.aggregate(Sum('fighters'))['fighters__sum']
        totcor = fleet.objects.aggregate(Sum('corvettes'))['corvettes__sum']
        totlcr = fleet.objects.aggregate(Sum('light_cruisers'))['light_cruisers__sum']
        totdes = fleet.objects.aggregate(Sum('destroyers'))['destroyers__sum']
        totfri = fleet.objects.aggregate(Sum('frigates'))['frigates__sum']
        tothcr = fleet.objects.aggregate(Sum('heavy_cruisers'))['heavy_cruisers__sum']
        totbcr = fleet.objects.aggregate(Sum('battlecruisers'))['battlecruisers__sum']
        totbsh = fleet.objects.aggregate(Sum('battleships'))['battleships__sum']
        totdre = fleet.objects.aggregate(Sum('dreadnoughts'))['dreadnoughts__sum']
        totwar = World.objects.aggregate(Sum('warpoints'))['warpoints__sum']
        totfree = World.objects.filter(econsystem=1).count()
        totmixed = World.objects.filter(econsystem=0).count()
        totcp = World.objects.filter(econsystem=-1).count()
        totlibdem = World.objects.filter(polsystem__gte=60).count()
        totauthdem = World.objects.filter(polsystem__lt=60, polsystem__gt=20).count()
        totsingle = World.objects.filter(polsystem__lte=20, polsystem__gte=-20).count()
        totadmiralty = World.objects.filter(polsystem__lt=-20, polsystem__gt=-60).count()
        totauto = World.objects.filter(polsystem__lte=-60).count()
        corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()
        totfiglvl = World.objects.filter(millevel__lt=corlevel).count()
        totcorlvl = World.objects.filter(millevel__lt=lcrlevel, millevel__gte=corlevel).count()
        totlcrlvl = World.objects.filter(millevel__lt=deslevel, millevel__gte=lcrlevel).count()
        totdeslvl = World.objects.filter(millevel__lt=frilevel, millevel__gte=deslevel).count()
        totfrilvl = World.objects.filter(millevel__lt=hcrlevel, millevel__gte=frilevel).count()
        tothcrlvl = World.objects.filter(millevel__lt=bcrlevel, millevel__gte=hcrlevel).count()
        totbcrlvl = World.objects.filter(millevel__lt=bshlevel, millevel__gte=bcrlevel).count()
        totbshlvl = World.objects.filter(millevel__lt=drelevel, millevel__gte=bshlevel).count()
        totdrelvl = World.objects.filter(millevel__gte=drelevel).count()
        stats = {'totworlds':totworlds, 'totA':totA, 'totB':totB, 'totC':totC, 'totD':totD, 'totGDP':totGDP, 'totbudget':totbudget,
            'totgrowth':totgrowth, 'totfuel':totfuel, 'totdur':totdur, 'tottrit':tottrit, 'totadam':totadam, 'totfuelprod':totfuelprod,
            'totdurprod':totdurprod, 'tottritprod':tottritprod, 'totadamprod':totadamprod, 'totfig':totfig, 'totcor':totcor,
            'totlcr':totlcr, 'totdes':totdes, 'totfri':totfri, 'tothcr':tothcr, 'totbcr':totbcr, 'totbsh':totbsh, 'totdre':totdre,
            'totwar':totwar, 'totfreighters':totfreighters, 'totfree':totfree, 'totmixed':totmixed, 'totcp':totcp, 'totlibdem':totlibdem,
            'totauthdem':totauthdem, 'totsingle':totsingle, 'totadmiralty':totadmiralty, 'totauto':totauto, 'totshipyards':totshipyards,
            'totfiglvl':totfiglvl, 'totcorlvl':totcorlvl, 'totlcrlvl':totlcrlvl, 'totdeslvl':totdeslvl, 'totfrilvl':totfrilvl,
            'tothcrlvl':tothcrlvl, 'totbcrlvl':totbcrlvl, 'totbshlvl':totbshlvl, 'totdrelvl':totdrelvl}
        cache.set('statistics', stats, 60*30) # not calculating this on every page refresh
    
    data = GlobalData.objects.get(pk=1)
    rumsoddium = data.rumsoddiumwars

    if len(rsowners) == 1:
        rsamount = 'This world has'
    elif len(rsowners) == 2:
        rsamount = 'These two worlds have'
    elif len(rsowners) == 3:
        rsamount = 'These three worlds have'
    elif len(rsowners) == 4:
        rsamount = 'These four worlds have'
    else:
        rsamount = None

    return render(request, 'galactic_news.html', {'wars':wars, 'announcements':announcements, 'message':message, 'displayform':displayform,
        'rsowners':rsowners, 'rumsoddium':rumsoddium, 'counttext':counttext,
        'rsamount':rsamount, 'stats':stats})


@login_required
@world_required
def tasks(request):
    'View and revoke tasks here.'
    world = request.user.world
    revoked = 0

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes tasks by checkbox
            listitems = request.POST.getlist('taskitem')
            for i in listitems:
                try:
                    item = Task.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.target == world and item.datetime < v.now():
                        item.delete()

        if "revoke" in form:
            listitems = request.POST.getlist('taskitem')
            for i in listitems:
                try:
                    item = Task.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.target == world and item.revokable:
                        revoked += 1
                        item.delete()

        if "deleteall" in form:   # deletes all tasks
            listitems = Task.objects.filter(target=world, datetime__lt=v.now()).delete()

    tasks = []
    completedtasks = []
    revokable = 0
    for i in Task.objects.filter(target=world).order_by('-datetime'):  # reverse chrono order
        if i.datetime < v.now():
            completedtasks.append(i)
        else:
            timedifference = i.datetime - v.now()
            hours, minutes, seconds = utilities.timedeltadivide(timedifference)
            tasks.append({'data':i,'hours':hours, 'minutes':minutes, 'seconds':seconds})
            if i.revokable:
                revokable += 1

    if len(completedtasks) == 0:
        completedtasks = None
    if len(tasks) == 0:   # Displays 'no tasks'
        tasks = None

    return render(request, 'tasks.html', {'tasks': tasks,'completedtasks':completedtasks,'revokable':revokable,'revoked':revoked})


@login_required
@world_required
def communiques(request):
    'View/delete comms here.'
    world = request.user.world

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('commitem')
            for i in listitems:
                try:
                    item = Comm.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.target == world:
                        item.delete()

        if "deleteall" in form:   # deletes all news
            Comm.objects.filter(target=world).delete()

        if "deletebyworld" in form:
            pk = form["target"]
            try:
                target = World.objects.get(pk=pk)
            except ObjectDoesNotExist:
                pass
            else:
                Comm.objects.filter(target=world).filter(sender=target).delete()

    commslist = list(Comm.objects.filter(target=world).order_by('-datetime'))  # reverse chrono order
    Comm.objects.filter(target=world).update(seen=True)
    deleteform = DeleteByTargetForm(world, 'reccomm')

    if len(commslist) == 0:   # Displays 'no comms'
        commslist = None

    if world.commpref == 'old':
        return render(request, 'communiquesold.html', {'comms': commslist, 'deleteform':deleteform})
    else:
        if commslist is None:
            commslist = []
        commsdict = OrderedDict()
        numberlist = []
        unreadlist = []
        unreadstring = ''
        for comm in commslist:
            try:
                commsdict[comm.sender].append(comm)
            except KeyError:
                commsdict[comm.sender] = [comm]
            if not comm.seen and comm.sender.name not in unreadlist:
                unreadlist.append(comm.sender.name)
        for name in commsdict:
            numberlist.append(len(commsdict[name]))
        if len(commslist) == 0:   # Displays 'no comms'
            commsdict = None

        for name in unreadlist:
            unreadstring += name + ','

        return render(request, 'communiques.html', {'commsdict':commsdict,'numberlist':numberlist,'unread':unreadstring, 'deleteform':deleteform})


@login_required
@world_required
def sentcomms(request):
    'View/delete sent comms here.'
    world = request.user.world

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('commitem')
            for i in listitems:
                item = SentComm.objects.get(pk=int(i))
                if item.sender == world:
                    item.delete()

        if "deleteall" in form:   # deletes all news
            SentComm.objects.filter(sender=world).delete()

        if "deletebyworld" in form:
            pk = form["target"]
            try:
                target = World.objects.get(pk=pk)
            except ObjectDoesNotExist:
                pass
            else:
                SentComm.objects.filter(target=target, sender=world).delete()

    commslist = list(SentComm.objects.filter(sender=world).order_by('-datetime'))  # reverse chrono order
    deleteform = DeleteByTargetForm(world, 'sentcomm')

    if world.commpref == 'old':
        return render(request, 'sentcommsold.html', {'comms': commslist, 'deleteform':deleteform})
    else:
        commsdict = OrderedDict()
        numberlist = []
        for comm in commslist:
            try:
                commsdict[comm.target].append(comm)
            except KeyError:
                commsdict[comm.target] = [comm]
        for name in commsdict:
            numberlist.append(len(commsdict[name]))
        if len(commslist) == 0:   # Displays 'no comms'
            commsdict = None

        return render(request, 'sentcomms.html', {'commsdict':commsdict,'numberlist':numberlist, 'deleteform':deleteform})


@login_required
@world_required
def newtrade(request):
    'Propose a new trade here.'
    world = request.user.world
    if v.now() < world.warprotection:
        warprotection = True
    cost = 5 * (world.econsystem + 3)
    message = warprotection = indefwar = form = btnval = trade = None
    tempmsg = ""
    actions = {}
    init = {
    'offer_amount': 1,
    'request_amount': 1,
    'amount': 1,
    }
    if world.wardefender.count() > 0:
        indefwar = True
    if world.gdp < 250:
        return redirect('trades')
    if request.method == 'POST':
        if 'newtrade' in request.POST: #different postans
            if request.POST['newtrade'] == 'blueprint':
                form = Blueprinttradeform(world, initial=init)
            elif request.POST['newtrade'] == 'ship':
                form = Shiptradeform(world, initial=init)
            else:
                form = Resourcetradeform(world, initial=init)
            btnval = request.POST['newtrade']

        elif 'ship' in request.POST:
            form = Shiptradeform(world, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                shiptype = data['offer']
                if data['fleet'].__dict__[shiptype] < data['amount']:
                    message = "%s doesn't have enough %s!" % (data['fleet'].name, shiptype.replace('_', ' '))
                else:
                    trade = Trade.objects.create(owner=world, amount=data['amount'],
                        offer=shiptype, offer_amount=data['amount'], offer_type='ship',
                        fleet_source=data['fleet'], 
                        request=data['request'], request_amount=data['request_amount'])
                    if v.now() < world.warprotection:
                        actions.update({
                            'warprotection': {'action': 'set', 'amount': v.now()},
                            'noobprotect': {'action': 'set', 'amount': False}
                        })
                        tempmsg += '<br>Your war protection is now over.'

        elif 'blueprint' in request.POST:
            form = Blueprinttradeform(world, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                bptype = Blueprint_license.objects.get(pk=data['offer']).model
                if data['amount'] > len(world.blueprints.all().filter(model=bptype)):
                    message = "You do not have that many blueprints avaliable!"
                else:
                    trade = Trade.objects.create(owner=world, amount=data['amount'],
                        offer="blueprint", offer_amount=data['offer_amount'], offer_type="blueprint",
                        request=data['request'], request_amount=data['request_amount'],
                        blueprint_type=bptype, blueprint_pk=data['offer'])

        elif 'resource' in request.POST:
            form = Resourcetradeform(world, request.POST)
            if form.is_valid():
                data = form.cleaned_data
                resource = data['offer']
                #gonna need to move this type of verification to form level
                if data['amount'] * data['offer_amount'] > world.__dict__[resource]:
                    if resource == "budget":
                        message = "You don't have that many GEU!"
                    else:
                        message = "You don't have that much %s!" % resource
                elif data['offer'] == data['request']:
                    message = "You need to trade different resources"
                else:
                    trade = Trade.objects.create(owner=world, amount=data['amount'],
                        offer=data['offer'], offer_amount=data['offer_amount'],
                        request=data['request'], request_amount=data['request_amount'])

        elif 'None' in request.POST:
            return redirect('trades')
        if trade != None:
            tempmsg = 'Trade posted.' + tempmsg
            actions.update({'tempmsg': {'action': 'set', 'amount': tempmsg}})
            utilities.atomic_world(world.pk, actions)
            return redirect('trades')
    else:
        return redirect('trades')
    return render(request, 'newtrade.html', {'form': form, 'btnval': btnval, 'cost':cost, 'message':message, 'warprotection':warprotection, 'indefwar':indefwar})


@login_required
@world_required
def trades(request):
    'Accept/delete/modify a trade here.'
    world = request.user.world
    blueprints = (True if Blueprint_license.objects.filter(owner=world).count() > 0 else False)
    warprotection = indefwar = None
    endprotect = ''
    message = world.tempmsg
    if world.tempmsg != None:
        world.tempmsg = None
        world.save(update_fields=['tempmsg'])

    if request.method == 'POST':
        form = request.POST
        message = None
        actions = {}
        if "delete" in form:
            try:
                world.trades.all().get(pk=request.POST['delete']).delete()
            except ObjectDoesNotExist:
                message = "Trade does not exist!"

        if "modify" in form:
            try:
                trade = world.trades.all().get(pk=request.POST['modify'])
            except:
                message = "That trade does not exist!"
            else:
                form = tradeamountform(trade, request.POST)
                if form.is_valid():
                    trade.amount = form.cleaned_data['tradeno']
                    trade.save()
                    message = "Trade modified."
                    if trade.offer_type == 'ship':
                        if v.now() < world.warprotection:
                            actions.update({
                                'warprotection': {'action': 'set', 'amount': v.now()},
                                'noobprotect': {'action': 'set', 'amount': False},
                                })
                            message += '<br>Your war protection is now over.'
                        if world.wardefender.count() > 0:
                            stabchange = utilities.attrchange(world.stability, -5)
                            contchange = utilities.attrchange(world.contentment, -10)
                            actions.update({
                                'stability': {'action': 'add', 'amount': stabchange},
                                'contentment': {'action': 'add', 'amount': contchange},
                                })
                            message += '<br>You have lost perception and stability.'

        if "accept" in form:
            try:
                trade = Trade.objects.all().exclude(owner=world).get(pk=request.POST['accept'])
            except ObjectDoesNotExist:
                message = 'This trade is no longer available!'
            else:
                form = Accepttradeform(trade, request.POST)
                if form.is_valid():
                    tradeamount = form.cleaned_data['amount']
                    poster = trade.owner
                    posteractions = {}
                    total_out = trade.request_amount * tradeamount
                    total_in = trade.offer_amount * tradeamount
                    cost = (5 * (trade.owner.econsystem + 3)) * tradeamount
                    if trade.owner.budget < cost * tradeamount:
                        proceed = False
                        posteractions.update({'budget': {'action': 'subtract', 'amount': D(trade.owner.budget / 5)}})
                        reason = 'you did not have enough GEU to pay the upfront cost'
                        message = 'The world offering this trade cannot uphold it! It has been fined 20%% of its budget.'
                        htmldata = news.tradefail(reason)
                        NewsItem.objects.create(target=trade.owner, content=htmldata)
                        trade.delete()
                    else:
                        proceed = True #instead of ridiculously nested conditionals
                    if trade.offer_type == 'ship':
                        if not trade.owner.fleets.all().filter(controller=trade.owner, pk=trade.fleet_source.pk).exists():
                            proceed = False
                            trade.owner.trades.all().filter(pk=trade.fleet_source).delete()
                            message = "Unfortunately, the fleet sourcing the offered ships no longer exists."
                            content = "One of the fleets that contained ships put for sale in the market is no longer available.\
                                <br> All associated trades have been deleted."
                            NewItem.objects.create(target=trade.owner, content=content)


                    if trade.offer_type == 'resource' and proceed:
                        if trade.offer == 'budget':
                            required_freighters = utilities.freightercount(trade.request, trade.request_amount * tradeamount)
                        else:
                            required_freighters = utilities.freightercount(trade.offer, trade.offer_amount * tradeamount)
                        delay = (2 if world.sector == trade.owner.sector else 4)
                        outcometime = v.now() + time.timedelta(minutes=delay)
                        #first block handles money in resources out
                        if trade.offer == 'budget':
                            if world.__dict__[trade.request] < total_out:
                                message = "We do not have enough %s! We're %s short." % (trade.request, total_out - world.__dict__[trade.request])
                            elif world.freighters < required_freighters:
                                message = "We do not have enough freighters! We need %s more." % (int(required_freighters) - int(world.freighters))
                            elif trade.owner.budget < total_in + cost:
                                message = 'The world offering this trade cannot uphold it! It has been fined 20%% of its budget.'
                                posteractions.update({'budget': {'action': 'subtract', 'amount': D(trade.owner.budget / 5)}})
                                reason = 'you did not have enough GEU to pay the upfront cost'
                                htmldata = news.tradefail(reason)
                                NewsItem.objects.create(target=trade.owner, content=htmldata)
                                trade.delete()
                            else:
                                #subtract resource and freighters and exchange budget
                                actions.update({
                                    'budget': {'action': 'add', 'amount': total_in},
                                    'freighters': {'action': 'subtract', 'amount': required_freighters},
                                    'freightersinuse': {'action': 'add', 'amount': required_freighters},
                                    trade.request: {'action': 'subtract', 'amount': total_out},
                                    })
                                posteractions = {'budget': {'action': 'subtract', 'amount': total_in}}
                                utilities.atomic_world(poster.pk, posteractions)
                                utilities.atomic_world(world.pk, actions)
                                #now prepare the transfer
                                actions = {
                                    'freighters': {'action': 'add', 'amount': required_freighters},
                                    'freightersinuse': {'action': 'subtract', 'amount': required_freighters},
                                }
                                posteractions = {trade.request: {'action': 'add', 'amount': total_out}}
                                taskdetails = taskdata.tradeaccepterarrival(world, trade.displayrec, total_in)
                                task = Task.objects.create(target=poster, content=taskdetails, datetime=outcometime)
                                newtask.tradecomplete.apply_async(args=(world.pk, trade.owner.pk, 
                                        task.pk, trade.request, total_out, required_freighters), eta=outcometime)
                                log = ResourceLog.objects.create(owner=world, target=poster, trade=True)
                                Logresource.objects.create(log=log, resource='GEU', amount=total_in)
                                log2 = ResourceLog.objects.create(owner=poster, target=world, sent=True, trade=True)
                                Logresource.objects.create(log=log2, resource='GEU', amount=total_in)
                                Logresource.objects.create(log=log2, resource=trade.offer, amount=total_in)
                                trade.amount -= tradeamount

                        elif trade.owner.freighters < required_freighters:
                            message = 'The world offering this trade does not have the freighters to transport it! It has been fined 20%% of its budget.'
                            posteractions.update({'budget': {'action': 'subtract', 'amount': D(trade.owner.budget / 5)}})
                            htmldata = news.tradefailfreighters(trade.offer)
                            NewsItem.objects.create(target=trade.owner, content=htmldata)
                            trade.delete()
                            #here we handle money out resources in
                        else:
                            if world.__dict__[trade.request] < total_out:
                                rtype = ('GEU' if trade.request == 'budget' else trade.request)
                                message = "We do not have enough %s to accept this offer! We need %s more." % (rtype, total_out - world.__dict__[trade.request])
                            else:
                                actions.update({
                                    'budget': {'action': 'subtract', 'amount': total_out}
                                    })
                                posteractions.update({
                                    'budget': {'action': 'add', 'amount': total_out-cost},
                                    'freighters': {'action': 'subtract', 'amount': required_freighters},
                                    'freightersinuse': {'action': 'add', 'amount': required_freighters},
                                    trade.offer: {'action': 'subtract', 'amount': total_in},
                                    })
                                print poster.freighters, poster.duranium
                                print world.freighters, world.duranium
                                print actions
                                print required_freighters, total_out
                                utilities.atomic_world(poster.pk, posteractions)
                                utilities.atomic_world(world.pk, actions)
                                actions = {trade.offer: {'action': 'add', 'amount': total_in}}
                                posteractions = {
                                    'freighters': {'action': 'add', 'amount': required_freighters},
                                    'freightersinuse': {'action': 'subtract', 'amount': required_freighters},
                                    }
                                taskdetails = taskdata.tradeaccepterarrival(poster, trade.displayoff, total_in)
                                task = Task.objects.create(target=world, content=taskdetails, datetime=outcometime)
                                newtask.tradecomplete.apply_async(args=(trade.owner.pk, world.pk, 
                                    task.pk, trade.offer, total_in, required_freighters), eta=outcometime)
                                log = ResourceLog.objects.create(owner=poster, target=world, trade=True)
                                Logresource.objects.create(log=log, resource='GEU', amount=total_out)
                                log2 = ResourceLog.objects.create(owner=poster, target=world, trade=True)
                                Logresource.objects.create(log=log2, resource=trade.offer, amount=total_in)
                                log3 = ResourceLog.objects.create(owner=world, target=poster, sent=True, trade=True)
                                Logresource.objects.create(log=log3, resource='GEU', amount=total_out)
                                trade.amount -= tradeamount

                    elif trade.offer_type == "ship" and proceed:
                        ship = trade.offer
                        pship = ship.replace('_', ' ')
                        delay = (4 if world.sector == trade.owner.sector else 8)
                        if trade.offer == "freighters":
                            delay /= 2
                        outcometime = v.now() + time.timedelta(minutes=delay)
                        if trade.fleet_source.__dict__[ship] < total_in:
                            message = "Seller doesn't have enough ships and has been fined."
                            posteractions.update({'budget': {'action': 'subtract', 'amount': D(trade.owner.budget / 5)}})
                            trade.owner.trades.all().filter(fleet_source=trade.fleet_source).delete()
                        elif world.__dict__[trade.request] < total_out:
                            resource = ('GEU' if trade.request == 'budget' else trade.request)
                            message = "You do not have enough %s! You need %s more." % (resource, total_out - world.__dict__[ship])
                        else:
                            incoming = fleet()
                            incoming.__dict__[ship] = total_in
                            incoming.training = incoming.maxtraining() * trade.fleet_source.ratio()
                            tfactions = {'set': {
                            'training': trade.fleet_source.training - incoming.training,
                            ship: trade.fleet_source.__dict__[ship] - incoming.__dict__[ship],
                            }}
                            utilities.atomic_fleet(trade.fleet_source.pk, tfactions)
                            shipsin = "%s %s" % (total_in, ship)
                            taskdetails = taskdata.tradeaccepterarrival(poster, trade.displayoff, total_in)
                            task = Task.objects.create(target=world, content=taskdetails, datetime=outcometime)
                            newtask.shiptradecomplete.apply_async(args=(trade.owner.pk, world.pk, task.pk, shipsin, incoming.training), eta=outcometime)
                            log = ResourceLog.objects.create(owner=poster, target=world, trade=True)
                            Logresource.objects.create(log=log, resource='GEU', amount=total_out)
                            log2 = ResourceLog.objects.create(owner=poster, target=world, sent=True, trade=True)
                            Logresource.objects.create(log=log2, resource=pship, amount=total_in)
                            log3 = ResourceLog.objects.create(owner=world, target=poster, sent=True, trade=True)
                            Logresource.objects.create(log=log3, resource='GEU', amount=total_out)
                            trade.amount -= tradeamount

                        ##
                    tradelogger.info('---')
                    tradelogger.info('%s (id=%s) accepted trade with %s (id=%s),',
                        world.name, world.pk, trade.owner.name, trade.owner.pk)
                    tradelogger.info('sending %s %s and receiving %s %s',
                        total_out, trade.displayrec, total_in, trade.displayoff)


                    if trade.amount <= 0:
                        trade.delete()
                    else:
                        trade.save()
                    if message == None:
                        message = 'Trade accepted!' + endprotect
                else:
                    message = "error"
        world.refresh_from_db() #if post then we need fresh data

    trades = Trade.objects.all()
    len(trades) #single query
    owntradeslist = trades.filter(owner=world).order_by('-posted')
    tradeslist = trades.exclude(owner=world)
    names = v.resources + v.shipindices
    tradenames = v.tradenames
    renderlist = []
    for tradename, tradetype in zip(tradenames, names):
        trades = tradeslist.filter(offer=tradetype).order_by('-posted')
        if trades.count() == 0:
            continue
        tmprender = []
        for trade in trades:
            if trade.offer == 'budget':
                delay = 0
            elif trade.offer in v.shipindices:
                delay = (4 if world.sector == trade.owner.sector else 8)
            else:
                delay = (1 if world.sector == trade.owner.sector else 2)
            init = {'amount': 1}
            tmprender.append({'trade': trade, 'delay': delay, 'tradeform': Accepttradeform(trade, initial=init)})
        renderlist.append({'name': tradename, 'trades': tmprender})

    notrades = (True if len(tradeslist) == 0 else False)

    warprotection = (True if v.now() < world.warprotection else False)

    if not owntradeslist:
        owntradeslist = False

    indefwar = (True if world.wardefender.count() else False)

    return render(request, 'trades.html', {'owntrades':owntradeslist, 'message':message, 'warprotection':warprotection, 'notrades': notrades,
        'indefwar':indefwar, 'world': world, 'blueprints': blueprints, 'tradeslist':renderlist, 'tradenames':tradenames})


def stats(request):
    'Base stats page, redirects to 1st stats page'
    return redirect('statspage', 1)


def statspage(request, page):
    'Stats page, displays 20 worlds at a time. Searches by name'
    results = showform = world = None
    flagpref = 'new'
    displayno = 20
    logged_in = request.user.is_anonymous()
    try:
        world = World.objects.get(user=request.user)
    except:
        showform = None
        sortform = GalaxySortForm()
        sort = 'pk'
    else:
        if request.method == 'POST':
            form = request.POST
            if "selectsort" in form:
                form = GalaxySortForm(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    sortby = data['sortby']
                    if sortby in v.galsortprefs:
                        world.galaxysort = sortby
                        world.save()

        showform = True
        sortform = GalaxySortForm(initial={'sortby':world.galaxysort})
        sort = world.galaxysort
        flagpref = world.flagpref
        displayno = world.worlddisplayno

    if request.method == 'POST':
        form = request.POST
        if "search" in form:
            searchdata = form['searchdata']
            results = World.objects.filter(name__icontains=searchdata).exclude(pk=0)
            if len(results) == 0:
                results = None

    pages = []
    displayworlds = []
    worlds = list(World.objects.all().exclude(pk=0).order_by(sort))
    totalworlds = len(worlds)
    totalpages = int(totalworlds/displayno)+1
    pages = [i+1 for i in range(totalpages)]
    start = ((int(page)-1)*displayno)
    displayworlds = [i for i in worlds[start:start+displayno]]

    sortform = GalaxySortForm()
    if not logged_in:
        if World.objects.filter(user=request.user).exists():
            sortform = GalaxySortForm(initial={'sortby':world.galaxysort})

    if flagpref == 'old':
        flagpref = None

    return render(request, 'stats.html', {'worlds': displayworlds, 'pages': pages, 'results':results, 'showform':showform,
        'sortform':sortform, 'ownworld':world, 'current':int(page), 'flagpref': flagpref})


# stats_ind is in interactions.py


def alliances(request):
    'Base alliance page, redirects to 1st alliance page'
    return redirect('alliancespage', 1)


def alliancespage(request, page):
    'Alliance page, displays 20 alliances at a time.'

    pages = []
    displayalliances = []
    alliances = list(Alliance.objects.all())
    sortedalliances = sorted(alliances, key=utilities.allsize, reverse=True)
    totalalliances = len(alliances)
    totalpages = int(totalalliances/20)+1
    pages = [i+1 for i in range(totalpages)]
    start = ((int(page)-1)*20)
    for i in sortedalliances[start:start+20]:
        count = i.allmember.all().count()
        try:
            leader = i.allmember.get(leader=True)
        except:
            utilities.cleanalliance(i)
            return alliancespage(request,page)
        displayalliances.append({'data':i, 'leader':leader, 'count':count})
    return render(request, 'alliances.html', {'alliances': displayalliances, 'pages': pages, 'current':int(page)})


def alliances_ind(request, allid):
    'Display of an alliance.'

    message = displayentry = leave = None

    alliance, alliancemembs, officers, leader = utilities.alliancedata(request, allid)
    if alliance == None:
        return render(request, 'notfound.html', {'item': 'alliance'})

    try:                            # allows for display to non-user
        world = World.objects.get(user=request.user)
    except:
        world = None
    else:
        if world in alliance.invites.all():
            displayentry = True
            if request.method == 'POST':
                form = request.POST
                if "joinalliance" in form:
                    if world.alliance != None:
                        message = 'You are already in an alliance!'
                    else:
                        alliance.invites.remove(world)
                        alliance.save()
                        world.alliance = alliance
                        world.officer = False
                        world.leader = False
                        world.save(update_fields=['alliance','officer','leader'])
                        world.allianceinvites.clear()
                        AllianceLog.objects.create(alliance=alliance, world=world, logtype=2)
                        message = 'You have joined this federation.'
                        displayentry = None

        if request.method == 'POST' and world.alliance == alliance:
            form = request.POST

            if world.leader:

                if "demoteofficers" in form:
                    listofficers = request.POST.getlist('listofficers')
                    for i in listofficers:
                        item = World.objects.get(pk=int(i))
                        if item.alliance == alliance:
                            item.officer = False
                            item.save(update_fields=['officer'])
                            htmldata = news.officerdemotion()
                            NewsItem.objects.create(target=item, content=htmldata)
                            AllianceLog.objects.create(alliance=alliance,officer=world,world=item,logtype=4)

                if "promotemembers" in form:
                    listmembers = request.POST.getlist('listmembers')
                    for i in listmembers:
                        item = World.objects.get(pk=int(i))
                        if item.alliance == alliance:
                            item.officer = True
                            item.save(update_fields=['officer'])
                            htmldata = news.memberpromotion()
                            NewsItem.objects.create(target=item, content=htmldata)
                            AllianceLog.objects.create(alliance=alliance,officer=world,world=item,logtype=3)

                if "purgemembers" in form:
                    listmembers = request.POST.getlist('listmembers')
                    for i in listmembers:
                        item = World.objects.get(pk=int(i))
                        if item.alliance == alliance:
                            item.alliance = None
                            item.save(update_fields=['alliance'])
                            htmldata = news.purge(alliance)
                            NewsItem.objects.create(target=item, content=htmldata)
                            AllianceLog.objects.create(alliance=alliance,officer=world,world=item,logtype=6)

            if world.leader or world.officer:

                if "masscomm" in form:
                    commdata = form['commcontents']
                    if len(commdata) > 500:
                        message = 'Maximum 500 characters!'
                    else:
                        tosend = 'Alliance Mass Comm: ' + commdata
                        for item in alliance.allmember.all().iterator():
                            Comm.objects.create(target=item, sender=world, content=tosend)
                            message = 'Mass comm sent.'

                if "leadershipcomm" in form:
                    commdata = form['commcontents']
                    officerlist = ([] if officers == None else officers)
                    if len(commdata) > 500:
                        message = 'Maximum 500 characters!'
                    else:
                        tosend = 'Alliance Leadership Comm: ' + commdata
                        for item in officerlist+[leader]:
                            Comm.objects.create(target=item, sender=world, content=tosend)
                            message = 'Leadership comm sent.'

                if "withdraw" in form:
                    amount = form['withdrawamount']
                    try:
                        amount = D(amount)
                    except:
                        message = 'Enter a number.'
                    else:
                        if amount <= 0:
                            message = 'Enter a positive number.'
                        elif amount > alliance.bank:
                            message = 'You do not have enough money in your alliance bank!'
                        else:
                            amount = amount.quantize(D('.1'))
                            before = alliance.bank
                            after = before-amount
                            alliance.bank = F('bank') - amount
                            alliance.save(update_fields=['bank'])
                            world.budget = F('budget') + amount
                            world.save(update_fields=['budget'])
                            BankLog.objects.create(alliance=alliance, world=world, action=False, amount=amount, before=before, after=after)
                            if world.leader != True:
                                htmldata = news.withdrawalmade(world, amount)
                                NewsItem.objects.create(target=leader, content=htmldata)
                            message = 'GEUs withdrawn.'

            if "deposit" in form:
                amount = form['depositamount']
                try:
                    amount = D(amount)
                except:
                    message = 'Enter a whole number.'
                else:
                    if amount <= 0:
                        message = 'Enter a positive number.'
                    elif amount > world.budget:
                        message = 'You do not have enough money in your budget!'
                    else:
                        change = D(amount)*D(0.95)
                        change = change.quantize(D('.1'))
                        before = alliance.bank
                        after = alliance.bank + change
                        alliance.bank = F('bank') + change
                        alliance.save(update_fields=['bank'])
                        world.budget = F('budget') - amount
                        world.save(update_fields=['budget'])
                        BankLog.objects.create(alliance=alliance, world=world, action=True, amount=change, before=before, after=after)
                        if world.leader != True:
                            htmldata = news.depositmade(world, change)
                            NewsItem.objects.create(target=leader, content=htmldata)
                        message = 'GEUs deposited.'

            if "resignofficer" in form:
                if world.officer:
                    world.officer = False
                    world.save(update_fields=['officer'])
                    htmldata = news.resignation(world)
                    NewsItem.objects.create(target=leader, content=htmldata)
                    AllianceLog.objects.create(alliance=alliance, world=world, logtype=5)

            if "leavealliance" in form:
                if world.leader:
                    if alliancemembs == None and officers == None:
                        world.leader = False
                        world.alliance = None
                        world.save(update_fields=['leader','alliance'])
                        alliance.delete()
                        return redirect('main')
                    else:
                        message = 'You cannot leave an alliance that still has members!'
                if world.officer:
                    message = 'You cannot leave an alliance you are an officer of!'
                if world.leader == False and world.officer == False:
                    world.alliance = None
                    world.save(update_fields=['alliance'])
                    message = 'You have left this alliance.'
                    AllianceLog.objects.create(alliance=alliance, world=world, logtype=7)

        if world.alliance == alliance:
            if world.leader:
                if alliancemembs == None and officers == None:
                    leave = True
            if world.leader == False and world.officer == False:
                leave = True

        world.refresh_from_db()

    alliance, alliancemembs, officers, leader = utilities.alliancedata(request, allid)

    return render(request, 'alliances_ind.html', {'world': world, 'alliance': alliance,'leader': leader,
                                                  'officers': officers,'alliancemembs': alliancemembs,
                                                  'message': message, 'displayentry': displayentry,'leave':leave})


@login_required
@world_required
def alliances_logs(request, allid):
    'Displays alliance logs. Only leaders and officers allowed.'
    world = request.user.world
    alliance = Alliance.objects.get(allianceid=allid)

    if not (world.alliance == alliance and (world.officer or world.leader)):
        return redirect('main')
    else:
        loglist = list(BankLog.objects.filter(alliance=alliance).order_by('-datetime'))
        return render(request, 'alliances_logs.html', {'alliance':alliance,'loglist': loglist})


@login_required
@world_required
def alliances_memberlogs(request, allid):
    'Displays member logs. Only leaders and officers allowed.'
    world = request.user.world

    alliance = Alliance.objects.get(allianceid=allid)

    if not (world.alliance == alliance and (world.officer or world.leader)):
        return redirect('main')
    else:
        loglist = list(AllianceLog.objects.filter(alliance=alliance).order_by('-datetime'))
        return render(request, 'alliances_memberlogs.html', {'alliance':alliance,'loglist': loglist})


@login_required
@world_required
def alliances_admin(request, allid):
    'Admin an alliance here. Only leaders and officers allowed, with different functions.'
    world = request.user.world
    alliance = Alliance.objects.get(allianceid=allid)
    leader = None
    message = None

    if request.method == 'POST' and world.alliance == alliance:
        form = request.POST

        if world.leader:

            if "editdesc" in form:
                desc = form['description']
                if len(desc) > 300:
                    message = 'The description you entered is too long. Max 300 characters.'
                else:
                    alliance.alliance_desc = desc
                    alliance.save(update_fields=['alliance_desc'])

            if "setcustomflag" in form:
                customflag = form['customflag']
                alliance.alliance_flag = customflag
                alliance.save(update_fields=['alliance_flag'])

            if "setcustomanthem" in form:
                customanthem = form['customanthem']
                alliance.alliance_anthem = customanthem
                alliance.save(update_fields=['alliance_anthem'])

            if "setsuccessor" in form:
                name = form['successorname']
                try:
                    successor = World.objects.get(name=name)
                except:
                    message = 'No such world exists!'
                else:
                    if successor.alliance != alliance:
                        message = 'This world is not in your alliance!'
                    else:
                        successor.officer = False
                        successor.leader = True
                        successor.save(update_fields=['leader','officer'])
                        world.leader = False
                        world.save(update_fields=['leader'])
                        htmldata = news.successor(world)
                        NewsItem.objects.create(target=successor, content=htmldata)
                        AllianceLog.objects.create(alliance=alliance, officer=world, world=successor, logtype=8)
                        return redirect('alliances_ind',allid)

            if "setdisplayprefs" in form:
                listprefs = request.POST.getlist('displaypref')
                leaderlist = []
                officer = []
                member = []
                public = []
                check = True
                onlyone = 'You can only select one option in each category!'
                general = economic = resources = military = econtypes = poltypes = millevels = 0
                for pref in listprefs:
                    if pref not in v.alliancestatprefs:
                        check = False
                    elif 'general' in pref:
                        general += 1
                    elif 'economic' in pref:
                        economic += 1
                    elif 'resources' in pref:
                        resources += 1
                    elif 'military' in pref:
                        military += 1
                    elif 'econtypes' in pref:
                        econtypes += 1
                    elif 'poltypes' in pref:
                        poltypes += 1
                    elif 'millevels' in pref:
                        millevels += 1

                    if 'officer' in pref:
                        officer.append(pref)
                    elif 'member' in pref:
                        member.append(pref)
                    elif 'public' in pref:
                        public.append(pref)
                    else:
                        leaderlist.append(pref)

                if len(listprefs) != 7:
                    message = 'You must select one option per category.'
                elif not check:
                    message = 'You have selected an invalid preference!'
                elif general != 1:
                    message = onlyone
                elif economic != 1:
                    message = onlyone
                elif resources != 1:
                    message = onlyone
                elif military != 1:
                    message = onlyone
                elif econtypes != 1:
                    message = onlyone
                elif poltypes != 1:
                    message = onlyone
                elif millevels != 1:
                    message = onlyone
                else:
                    leaderprefs = ','.join(leaderlist)
                    officerprefs = ','.join(officer)
                    memberprefs = ','.join(member)
                    publicprefs = ','.join(public)
                    alliance.leaderstats = leaderprefs
                    alliance.officerstats = officerprefs
                    alliance.memberstats = memberprefs
                    alliance.publicstats = publicprefs
                    alliance.save(update_fields=['leaderstats','officerstats','memberstats','publicstats'])
                    message = 'Preferences updated.'

        if world.leader or world.officer:

            if "revokeinvite" in form:
                listinvites = request.POST.getlist('listinvites')
                for i in listinvites:
                    item = World.objects.get(pk=int(i))
                    if item in alliance.invites.all():
                        alliance.invites.remove(item)
                        alliance.save()
                        AllianceLog.objects.create(alliance=alliance, officer=world, world=item, logtype=1)

            if "invite" in form:
                name = form['name']
                try:
                    invitee = World.objects.get(name=name)
                except:
                    message = 'No such world exists!'
                else:
                    if invitee.alliance == alliance:
                        message = 'This world is already in your federation!'
                    else:
                        alliance.invites.add(invitee)
                        alliance.save()
                        htmldata = news.allianceinvite(alliance, world)
                        NewsItem.objects.create(target=invitee, content=htmldata)
                        AllianceLog.objects.create(alliance=alliance, officer=world, world=invitee, logtype=0)
                        message = 'Invite sent.'

    if not (world.alliance == alliance and (world.officer or world.leader)):
        invitelist = None
        return redirect('main')
    else:
        invitelist = list(alliance.invites.all())

    if world.leader:
        leader = True

    prefs = ','.join([alliance.leaderstats, alliance.officerstats, alliance.memberstats, alliance.publicstats])

    typelist = [('general','general'), ('economic','economic'), ('resource','resources'), ('military','military'),
        ('economic type','econtypes'), ('political type','poltypes'), ('military level','millevels')]

    return render(request, 'alliances_admin.html', {'alliance':alliance,'invitelist': invitelist, 'leader':leader, 'message':message,
        'prefs':prefs, 'typelist': typelist})


@login_required
@world_required
def alliances_stats(request, allid):
    'Displays stats of an alliance.'
    world = request.user.world

    alliance = Alliance.objects.get(allianceid=allid)
    leader = officer = member = None
    generaldisp = economicdisp = resourcesdisp = militarydisp = econtypesdisp = poltypesdisp = millevelsdisp = None

    if world.leader:
        leader = True
    elif world.officer:
        officer = True
    elif world in alliance.allmember.all():
        member = True

    totworlds = alliance.allmember.all().count()
    totA = alliance.allmember.all().filter(sector='amyntas').count()
    totB = alliance.allmember.all().filter(sector='bion').count()
    totC = alliance.allmember.all().filter(sector='cleon').count()
    totD = alliance.allmember.all().filter(sector='draco').count()
    totGDP = alliance.allmember.all().aggregate(Sum('gdp'))['gdp__sum']
    totbudget = alliance.allmember.all().aggregate(Sum('budget'))['budget__sum']
    totgrowth = alliance.allmember.all().aggregate(Sum('growth'))['growth__sum']
    totfuel = alliance.allmember.all().aggregate(Sum('warpfuel'))['warpfuel__sum']
    totdur = alliance.allmember.all().aggregate(Sum('duranium'))['duranium__sum']
    tottrit = alliance.allmember.all().aggregate(Sum('tritanium'))['tritanium__sum']
    totadam = alliance.allmember.all().aggregate(Sum('adamantium'))['adamantium__sum']
    totfuelprod = alliance.allmember.all().aggregate(Sum('warpfuelprod'))['warpfuelprod__sum']
    totdurprod = alliance.allmember.all().aggregate(Sum('duraniumprod'))['duraniumprod__sum']
    tottritprod = alliance.allmember.all().aggregate(Sum('tritaniumprod'))['tritaniumprod__sum']
    totadamprod = alliance.allmember.all().aggregate(Sum('adamantiumprod'))['adamantiumprod__sum']
    totfreighters =fleet.objects.filter(world__alliance=alliance).aggregate(Sum('freighters'))['freighters__sum'] 
    totshipyards = alliance.allmember.all().aggregate(Sum('shipyards'))['shipyards__sum']
    totfig = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('fighters'))['fighters__sum']
    totcor = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('corvettes'))['corvettes__sum']
    totlcr = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('light_cruisers'))['light_cruisers__sum']
    totdes = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('destroyers'))['destroyers__sum']
    totfri = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('frigates'))['frigates__sum']
    tothcr = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('heavy_cruisers'))['heavy_cruisers__sum']
    totbcr = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('battlecruisers'))['battlecruisers__sum']
    totbsh = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('battleships'))['battleships__sum']
    totdre = fleet.objects.filter(world__alliance=alliance).aggregate(Sum('dreadnoughts'))['dreadnoughts__sum'] 
    totwar = alliance.allmember.all().aggregate(Sum('warpoints'))['warpoints__sum'] 
    totfree = alliance.allmember.filter(econsystem=1).count()
    totmixed = alliance.allmember.filter(econsystem=0).count()
    totcp = alliance.allmember.filter(econsystem=-1).count()
    totlibdem = alliance.allmember.filter(polsystem__gte=60).count()
    totauthdem = alliance.allmember.filter(polsystem__lt=60, polsystem__gt=20).count()
    totsingle = alliance.allmember.filter(polsystem__lte=20, polsystem__gte=-20).count()
    totadmiralty = alliance.allmember.filter(polsystem__lt=-20, polsystem__gt=-60).count()
    totauto = alliance.allmember.filter(polsystem__lte=-60).count()
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()
    totfiglvl = alliance.allmember.filter(millevel__lt=corlevel).count()
    totcorlvl = alliance.allmember.filter(millevel__lt=lcrlevel, millevel__gte=corlevel).count()
    totlcrlvl = alliance.allmember.filter(millevel__lt=deslevel, millevel__gte=lcrlevel).count()
    totdeslvl = alliance.allmember.filter(millevel__lt=frilevel, millevel__gte=deslevel).count()
    totfrilvl = alliance.allmember.filter(millevel__lt=hcrlevel, millevel__gte=frilevel).count()
    tothcrlvl = alliance.allmember.filter(millevel__lt=bcrlevel, millevel__gte=hcrlevel).count()
    totbcrlvl = alliance.allmember.filter(millevel__lt=bshlevel, millevel__gte=bcrlevel).count()
    totbshlvl = alliance.allmember.filter(millevel__lt=drelevel, millevel__gte=bshlevel).count()
    totdrelvl = alliance.allmember.filter(millevel__gte=drelevel).count()

    general = ['<td>Amyntas Worlds:</td><td>%s</td>' % totA, '<td>Bion Worlds:</td><td>%s</td>' % totB,
        '<td>Cleon Worlds:</td><td>%s</td>' % totC, '<td>Draco Worlds:</td><td>%s</td>' % totD]

    economic = ['<td>GDP:</td><td>%s million GEU</td>' % totGDP, '<td>Budget:</td><td>%s GEU</td>' % totbudget,
        '<td>Growth:</td><td>%s million GEU</td>' % totgrowth]

    resources = ['<td>Warpfuel Supply:</td><td>%s</td>' % totfuel, '<td>Warpfuel Production:</td><td>%s per turn</td>' % totfuelprod,
        '<td>Duranium Supply:</td><td>%s</td>' % totdur, '<td>Duranium Production:</td><td>%s per turn</td>' % totdurprod,
        '<td>Tritanium Supply:</td><td>%s</td>' % tottrit, '<td>Tritanium Production:</td><td>%s per turn</td>' % tottritprod,
        '<td>Adamantium Supply:</td><td>%s</td>' % totadam, '<td>Adamantium Production:</td><td>%s per turn</td>' % totadamprod,
        '<td>Total Freighters:</td><td>%s</td>' % totfreighters]

    military = ['<td>Shipyards:</td><td>%s</td>' % totshipyards, '<td>Fighters:</td><td>%s</td>' % totfig,
        '<td>Corvettes:</td><td>%s</td>' % totcor, '<td>Light Cruisers:</td><td>%s</td>' % totlcr,
        '<td>Destroyers:</td><td>%s</td>' % totdes, '<td>Frigates:</td><td>%s</td>' % totfri,
        '<td>Heavy Cruisers:</td><td>%s</td>' % tothcr, '<td>Battlecruisers:</td><td>%s</td>' % totbcr,
        '<td>Battleships:</td><td>%s</td>' % totbsh, '<td>Dreadnoughts:</td><td>%s</td>' % totdre,
        '<td>Warpoints:</td><td>%s</td>' % totwar]

    econtypes = ['<td>Free Market Worlds:</td><td>%s</td>' % totfree, '<td>Mixed Economy Worlds:</td><td>%s</td>' % totmixed,
        '<td>Central Planning Worlds:</td><td>%s</td>' % totcp]

    poltypes = ['<td>Liberal Democracies:</td><td>%s</td>' % totlibdem, '<td>Totalitarian Democracies:</td><td>%s</td>' % totauthdem,
        '<td>Single-Party Worlds:</td><td>%s</td>' % totsingle, '<td>Fleet Admiralty Worlds:</td><td>%s</td>' % totadmiralty,
        '<td>Autocracies:</td><td>%s</td>' % totauto]

    millevels = ['<td>Worlds at Fighter level:</td><td>%s</td>' % totfiglvl, '<td>Worlds at Corvette level:</td><td>%s</td>' % totcorlvl,
        '<td>Worlds at Light Cruiser level:</td><td>%s</td>' % totlcrlvl, '<td>Worlds at Destroyer level:</td><td>%s</td>' % totdeslvl,
        '<td>Worlds at Frigate level:</td><td>%s</td>' % totfrilvl, '<td>Worlds at Heavy Cruiser level:</td><td>%s</td>' % tothcrlvl,
        '<td>Worlds at Battlecruiser level:</td><td>%s</td>' % totbcrlvl, '<td>Worlds at Battleship level:</td><td>%s</td>' % totbshlvl,
        '<td>Worlds at Dreadnought level:</td><td>%s</td>' % totdrelvl]

    generaldisp = utilities.alliancestats(world, alliance, leader, officer, member, 'general')
    economicdisp = utilities.alliancestats(world, alliance, leader, officer, member, 'economic')
    resourcesdisp = utilities.alliancestats(world, alliance, leader, officer, member, 'resources')
    militarydisp = utilities.alliancestats(world, alliance, leader, officer, member, 'military')
    econtypesdisp = utilities.alliancestats(world, alliance, leader, officer, member, 'econtypes')
    poltypesdisp = utilities.alliancestats(world, alliance, leader, officer, member, 'poltypes')
    millevelsdisp = utilities.alliancestats(world, alliance, leader, officer, member, 'millevels')

    return render(request, 'alliances_stats.html', {'alliance':alliance,'leader':leader, 'totworlds':totworlds,'general':general,
        'economic':economic, 'resources':resources, 'military':military, 'econtypes':econtypes, 'poltypes':poltypes, 'millevels':millevels,
        'generaldisp':generaldisp, 'economicdisp':economicdisp, 'resourcesdisp':resourcesdisp, 'militarydisp':militarydisp,
        'econtypesdisp':econtypesdisp, 'poltypesdisp':poltypesdisp, 'millevelsdisp':millevelsdisp})


@login_required
@world_required
def new_alliance(request):
    'New alliance page, checks if the world has not got an alliance and if fee to create paid.'
    world = request.user.world
    message = None

    if world.alliance != None:
        return redirect('main')
    else:
        if world.alliancepaid == False:
            return redirect('main')
        if request.method == 'POST':
            form = request.POST
            name = form['name']
            desc = form['description']
            if len(name) > 20:
                message = 'Your alliance name is too long! Maximum 20 characters.'
            elif len(name) < 3:
                message = 'Your alliance name is too short! Minimum 3 characters.'
            elif len(desc) > 200:
                message = 'Your alliance description is too long! Maximum 200 characters.'
            else:
                try:
                    newalliance = Alliance(alliance_name=name, alliance_desc=desc)
                    newalliance.save()
                except:
                    message = 'That alliance name is already in use! Pick another.'
                world.alliancepaid = False
                world.alliance = newalliance
                world.leader = True
                world.save(update_fields=['alliancepaid','alliance','leader'])
                return redirect('alliances_ind', allid=newalliance.pk)

    return render(request, 'newalliance.html', {'message': message})


# policies are in policies.py