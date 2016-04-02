# Django Imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import F
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

# Python Imports
from collections import OrderedDict
import random, decimal
import datetime as time

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

'''
The main file. Most page functions are carried out here.
'''

D = decimal.Decimal


def index(request):
    'Front page.'
    donators = cache.get('donators') # no need to
    if not donators:
        donators = list(World.objects.filter(donator=True).exclude(worldid=1))
        cache.set('donators', donators, 60 * 60 * 24)
    return render(request, 'index.html', {'donators': donators})


@login_required
@world_required
def main(request, world, message=None):
    'Main page: user\'s world.'

    haswars = offlist = deflist = None
    warprotection = abovegdpprotection = brokenwarprotect = None

    ip = request.META.get('REMOTE_ADDR')
    world.lastloggedinip = ip
    world.lastloggedintime = v.now()
    world.save(update_fields=['lastloggedinip', 'lastloggedintime'])

    if world.warattacker.count() > 0 or world.wardefender.count() > 0:
        haswars = True
        offlist = [war.defender for war in world.warattacker.all()]
        deflist = [war.attacker for war in world.wardefender.all()]

    displaybuilds = [False for i in range(9)]
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()

    if world.millevel >= drelevel:
        limit = 9
        millevel = 'Dreadnought'
        progress = None
    elif world.millevel >= bshlevel:
        limit = 9
        millevel = 'Battleship'
        progress = (world.millevel - bshlevel)/float(drelevel - bshlevel)
    elif world.millevel >= bcrlevel:
        limit = 8
        millevel = 'Battlecruiser'
        progress = (world.millevel - bcrlevel)/float(bshlevel - bcrlevel)
    elif world.millevel >= hcrlevel:
        limit = 7
        millevel = 'Heavy Cruiser'
        progress = (world.millevel - hcrlevel)/float(bcrlevel - hcrlevel)
    elif world.millevel >= frilevel:
        limit = 6
        millevel = 'Frigate'
        progress = (world.millevel - frilevel)/float(hcrlevel - frilevel)
    elif world.millevel >= deslevel:
        limit = 5
        millevel = 'Destroyer'
        progress = (world.millevel - deslevel)/float(frilevel - deslevel)
    elif world.millevel >= lcrlevel:
        limit = 4
        millevel = 'Light Cruiser'
        progress = (world.millevel - lcrlevel)/float(deslevel - lcrlevel)
    elif world.millevel >= corlevel:
        limit = 3
        millevel = 'Corvette'
        progress = (world.millevel - corlevel)/float(lcrlevel - corlevel)
    else:
        limit = 2
        millevel = 'Fighter'
        progress = world.millevel/float(corlevel)
    for index, value in enumerate(displaybuilds[:limit]):
        displaybuilds[index] = True

    if progress is not None:
        progress = int(100*progress/5.0)*5

    homeregion, staging, region1, region2, region3, hangars = utilities.mildisplaylist(world)

    world = World.objects.get(worldid=world.worldid)

    tooltips = utilities.tooltipdisplay(world)

    alliance = world.alliance
    current, maximum = utilities.trainingstatus(world, world.region)
    traininglevel = display.training_display(current, maximum)
    cansendpower = int(world.startpower*0.5) - world.powersent
    if cansendpower <= 0:
        cansendpower = 'None'
    shiploc = display.region_display(world.flagshiplocation)

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

    return render(request, 'main.html', {'world': world, 'alliance': alliance, 'millevel': millevel, 'displaybuilds':displaybuilds,
        'homeregion':homeregion, 'region1':region1, 'region2':region2, 'region3':region3, 'traininglevel':traininglevel, 'haswars':haswars,
        'offlist':offlist, 'deflist':deflist, 'progress':progress, 'tooltips':tooltips, 'warprotection':warprotection, 'message':message,
        'abovegdpprotection':abovegdpprotection, 'brokenwarprotect':brokenwarprotect, 'hangars':hangars, 'staging':staging,
        'cansendpower':cansendpower, 'shiploc':shiploc})


@login_required
@world_required
def spies(request, world):
    spieslist = list(Spy.objects.filter(owner=world))
    return render(request, 'spies.html', {'spieslist': spieslist})


@login_required
@world_required
def warlogs(request, world):

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('warlogitems')
            for i in listitems:
                try:
                    item = WarLog.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.owner == world:
                        item.delete()

        if "deleteall" in form:   # deletes all news
            WarLog.objects.filter(owner=world).delete()

        if "deletebyworld" in form:
            worldid = form["target"]
            try:
                target = World.objects.get(worldid=worldid)
            except ObjectDoesNotExist:
                pass
            else:
                WarLog.objects.filter(owner=world, target=target).delete()

    loglist = list(WarLog.objects.all().filter(owner=world).order_by('-datetime'))

    deleteform = DeleteByTargetForm(world, 'war')

    return render(request, 'warlogs.html', {'world':world,'loglist': loglist, 'deleteform':deleteform})


@login_required
@world_required
def reslogs(request, world):

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes news by checkbox
            listitems = request.POST.getlist('reslogitems')
            for i in listitems:
                try:
                    item = ResourceLog.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.owner == world:
                        item.delete()

        if "deleteall" in form:   # deletes all news
            ResourceLog.objects.filter(owner=world).delete()

        if "deletebyworld" in form:
            worldid = form["target"]
            try:
                target = World.objects.get(worldid=worldid)
            except ObjectDoesNotExist:
                pass
            else:
                ResourceLog.objects.filter(owner=world, target=target).delete()

    loglist = list(ResourceLog.objects.all().filter(owner=world).order_by('-datetime'))

    deleteform = DeleteByTargetForm(world, 'res')

    return render(request, 'reslogs.html', {'world':world,'loglist': loglist, 'deleteform':deleteform})


@login_required
def new_world(request):
    'New world page, only if the user has not already got a world.'

    message = None
    if World.objects.filter(worldid=request.user.id).exists():
        return redirect('main')
    else:
        if request.method == 'POST':
            form = NewWorldForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                worldname = data['worldname']
                regionin = data['region']
                if regionin not in v.sectors:
                    message = 'Sector choice error.'
                else:
                    econsysin = data['econsystem']
                    polsysin = data['polsystem']
                    ip = request.META.get('REMOTE_ADDR')
                    try:
                        newnation = World(worldid=request.user.id, creationip=ip, user_name=request.user.username,
                            world_name=worldname, region=regionin, econsystem=econsysin, polsystem=polsysin)
                        newnation.save()
                    except:
                        message = 'That world name is already in use! Pick another.'
                    else:
                        if regionin == 'A':
                            newnation.fighters_inA = 10
                            newnation.freighter_inA = 10
                            newnation.resource = random.randint(1,3)
                        elif regionin == 'B':
                            newnation.fighters_inB = 10
                            newnation.freighter_inB = 10
                            newnation.resource = random.randint(4,6)
                        elif regionin == 'C':
                            newnation.fighters_inC = 10
                            newnation.freighter_inC = 10
                            newnation.resource = random.randint(7,9)
                        elif regionin == 'D':
                            newnation.fighters_inD = 10
                            newnation.freighter_inD = 10
                            newnation.resource = random.randint(10,12)
                        if newnation.worldid in v.donatorlist:
                            newnation.donator = True
                        newnation.save()
                        for i in xrange(5):
                            agreement = Agreement(sender=newnation, receiver=newnation, order=-1, resource=newnation.resource)
                            agreement.save()
                        htmldata = news.newbevent(worldname)
                        ActionNewsItem.objects.create(target=newnation, content=htmldata, actiontype=2)
                        admin = World.objects.get(worldid=1)
                        Comm.objects.create(target=newnation, sender=admin, content=v.introcomm)
                        return redirect('main')
        else:
            form = NewWorldForm()

    return render(request, 'newworld.html', {'form': form,'message':message,'regiondata':v.regiondata,'econdata':v.econdata,'poldata':v.poldata})


@login_required
@world_required
def settings(request, world):
    'Users change settings here.'

    message = None
    invalid = 'Invalid preference selected.'

    if request.method == 'POST':
        form = request.POST

        if "editdesc" in form:
            desc = form['description']
            limit = (500 if world.donator else 300)
            if len(desc) > limit:
                message = 'The description you entered is too long.'
            elif '<' in desc or '>' in desc:
                message = 'The description contains invalid characters!'
            else:
                world.world_desc = desc
                world.save(update_fields=['world_desc'])
                message = 'Description changed.'

        if "setfleetnames" in form:
            listnames = request.POST.getlist('fleetname')
            toolong = 0
            for name in listnames:
                if len(name) > 15:
                    toolong += 1
            if toolong > 0:
                message = 'One of the fleet names you entered is too long.'
            else:
                world.fleetname_inA = listnames[0]
                world.fleetname_inB = listnames[1]
                world.fleetname_inC = listnames[2]
                world.fleetname_inD = listnames[3]
                world.fleetname_inH = listnames[4]
                world.fleetname_inS = listnames[5]
                world.save(update_fields=['fleetname_inA', 'fleetname_inB', 'fleetname_inC', 'fleetname_inD', 'fleetname_inH', 'fleetname_inS'])
                message = 'Fleet names changed.'

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
                    world.flag = flagid
                    world.save(update_fields=['flag'])
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
                    world.avatar = avatarid
                    world.save(update_fields=['avatar'])
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

        if world.donator:
            if "setcustomflag" in form:
                customflag = form['customflag']
                world.donatorflag = customflag
                world.save(update_fields=['donatorflag'])
                message = 'Flag changed.'

            if "setcustomavatar" in form:
                customavatar = form['customavatar']
                world.donatoravatar = customavatar
                world.save(update_fields=['donatoravatar'])
                message = 'Avatar changed.'

            if "setcustomanthem" in form:
                customanthem = form['customanthem']
                world.donatoranthem = customanthem
                world.save(update_fields=['donatoranthem'])
                message = 'Anthem changed.'

            if "setcustomps" in form:
                custompic = form['customps']
                world.donatorflagship = custompic
                world.save(update_fields=['donatorflagship'])
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

    world = World.objects.get(pk=world.pk)

    flagform = FlagForm(initial={'flag':world.flag})
    avatarform = AvatarForm(initial={'avatar':world.avatar})
    commform = CommDisplayForm(initial={'sortby':world.commpref})
    bgform = BackgroundForm(initial={'background':world.backgroundpref})
    policyform = PolicyChoiceForm(initial={'policychoice':world.policypref})
    shipform = ShipChoiceForm(initial={'buildchoice':world.buildpref})
    flagdisplayform = FlagDisplayForm(initial={'flagpref':world.flagpref})
    psform = PersonalShipPicForm(world.flagshiptype, initial={'pspic':world.flagshippicture})

    return render(request, 'settings.html', {'world': world, 'message': message,'flagform':flagform, 'avatarform':avatarform, 'commform':commform,
        'bgform':bgform, 'policyform':policyform, 'shipform':shipform, 'flagdisplayform':flagdisplayform, 'psform':psform,'test':str(world.backgroundpref)})


# world_news is in news.py


@login_required
@world_required
def tradecentre(request, world):
    'Display and admin trade agreements here.'

    message = None

    ownlist = utilities.getownlist(world)

    if request.method == 'POST':
        form = request.POST

        if "delete" in form:      # deletes by checkbox
            listitems = request.POST.getlist('notificationitems')
            for i in listitems:
                try:
                    item = AgreementLog.objects.get(pk=i)
                except ObjectDoesNotExist:
                    pass
                else:
                    if item.owner == world:
                        item.delete()

        if "deleteall" in form:
            AgreementLog.objects.filter(owner=world).delete()

        if "reorder" in form:
            listorders = request.POST.getlist('agreementorders')
            for index, value in enumerate(listorders):
                if value.lower() == 'last':
                    value = 0
                if not utilities.checkno(value, True):
                    message = 'Input numbers, or \'last\'.'
                else:
                    ownlist[index].order = value
                    ownlist[index].save(update_fields=['order'])

    maximum = 0
    lol = [] # list of lists

    for restype in xrange(1, 13):
        lol.append(list(Agreement.objects.filter(receiver=world, resource=restype)))

    for reslist in lol:
        if len(reslist) > maximum:
            maximum = len(reslist)
    if maximum > 12:
        maximum = 12

    totsurplus = world.resourceproduction - Agreement.objects.filter(sender=world).exclude(receiver=world).count()
    addsurplus = totsurplus - maximum
    if addsurplus < 0:
        addsurplus = 0

    if maximum == 0:
        maximum = 1
    maximum = range(maximum)

    growth, geu = turnupdates.grotrade(world)

    names = ['Salm.', 'Drones', 'Moss', 'Hfibres', 'Crystals', 'Arms', 'Conden.', 'Ch. Gas', 'Tet. Ore', 'Spiders', 'Holos', 'CPUs']

    loglist = list(AgreementLog.objects.filter(owner=world).order_by('-datetime'))

    ownlist = utilities.getownlist(world)

    return render(request, 'tradecentre.html', {'lol':lol, 'maximum':maximum, 'names':names, 'loglist':loglist, 'addsurplus':addsurplus,
        'econsys':world.econsystem, 'worldid':world.worldid, 'growth':growth, 'geu':geu, 'ownlist':ownlist, 'message':message,
        'totsurplus':totsurplus})


def galacticnews(request):
    'Galactic news - lottery, wars, announcements, stats.'

    message = None
    try:
        world = World.objects.get(worldid=request.user.id)
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
        totA = World.objects.filter(region='A').count()
        totB = World.objects.filter(region='B').count()
        totC = World.objects.filter(region='C').count()
        totD = World.objects.filter(region='D').count()
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
        totshipyards = World.objects.aggregate(Sum('shipyards'))['shipyards__sum']
        totfig = World.objects.aggregate(Sum('fighters_inA'))['fighters_inA__sum'] + \
            World.objects.aggregate(Sum('fighters_inB'))['fighters_inB__sum'] + \
            World.objects.aggregate(Sum('fighters_inC'))['fighters_inC__sum'] + \
            World.objects.aggregate(Sum('fighters_inD'))['fighters_inD__sum'] + \
            World.objects.aggregate(Sum('fighters_inS'))['fighters_inS__sum'] + \
            World.objects.aggregate(Sum('fighters_inH'))['fighters_inH__sum']
        totcor = World.objects.aggregate(Sum('corvette_inA'))['corvette_inA__sum'] + \
            World.objects.aggregate(Sum('corvette_inB'))['corvette_inB__sum'] + \
            World.objects.aggregate(Sum('corvette_inC'))['corvette_inC__sum'] + \
            World.objects.aggregate(Sum('corvette_inD'))['corvette_inD__sum'] + \
            World.objects.aggregate(Sum('corvette_inS'))['corvette_inS__sum'] + \
            World.objects.aggregate(Sum('corvette_inH'))['corvette_inH__sum']
        totlcr = World.objects.aggregate(Sum('light_cruiser_inA'))['light_cruiser_inA__sum'] + \
            World.objects.aggregate(Sum('light_cruiser_inB'))['light_cruiser_inB__sum'] + \
            World.objects.aggregate(Sum('light_cruiser_inC'))['light_cruiser_inC__sum'] + \
            World.objects.aggregate(Sum('light_cruiser_inD'))['light_cruiser_inD__sum'] + \
            World.objects.aggregate(Sum('light_cruiser_inS'))['light_cruiser_inS__sum'] + \
            World.objects.aggregate(Sum('light_cruiser_inH'))['light_cruiser_inH__sum']
        totdes = World.objects.aggregate(Sum('destroyer_inA'))['destroyer_inA__sum'] + \
            World.objects.aggregate(Sum('destroyer_inB'))['destroyer_inB__sum'] + \
            World.objects.aggregate(Sum('destroyer_inC'))['destroyer_inC__sum'] + \
            World.objects.aggregate(Sum('destroyer_inD'))['destroyer_inD__sum'] + \
            World.objects.aggregate(Sum('destroyer_inS'))['destroyer_inS__sum'] + \
            World.objects.aggregate(Sum('destroyer_inH'))['destroyer_inH__sum']
        totfri = World.objects.aggregate(Sum('frigate_inA'))['frigate_inA__sum'] + \
            World.objects.aggregate(Sum('frigate_inB'))['frigate_inB__sum'] + \
            World.objects.aggregate(Sum('frigate_inC'))['frigate_inC__sum'] + \
            World.objects.aggregate(Sum('frigate_inD'))['frigate_inD__sum'] + \
            World.objects.aggregate(Sum('frigate_inS'))['frigate_inS__sum'] + \
            World.objects.aggregate(Sum('frigate_inH'))['frigate_inH__sum']
        tothcr = World.objects.aggregate(Sum('heavy_cruiser_inA'))['heavy_cruiser_inA__sum'] + \
            World.objects.aggregate(Sum('heavy_cruiser_inB'))['heavy_cruiser_inB__sum'] + \
            World.objects.aggregate(Sum('heavy_cruiser_inC'))['heavy_cruiser_inC__sum'] + \
            World.objects.aggregate(Sum('heavy_cruiser_inD'))['heavy_cruiser_inD__sum'] + \
            World.objects.aggregate(Sum('heavy_cruiser_inS'))['heavy_cruiser_inS__sum'] + \
            World.objects.aggregate(Sum('heavy_cruiser_inH'))['heavy_cruiser_inH__sum']
        totbcr = World.objects.aggregate(Sum('battlecruiser_inA'))['battlecruiser_inA__sum'] + \
            World.objects.aggregate(Sum('battlecruiser_inB'))['battlecruiser_inB__sum'] + \
            World.objects.aggregate(Sum('battlecruiser_inC'))['battlecruiser_inC__sum'] + \
            World.objects.aggregate(Sum('battlecruiser_inD'))['battlecruiser_inD__sum'] + \
            World.objects.aggregate(Sum('battlecruiser_inS'))['battlecruiser_inS__sum'] + \
            World.objects.aggregate(Sum('battlecruiser_inH'))['battlecruiser_inH__sum']
        totbsh = World.objects.aggregate(Sum('battleship_inA'))['battleship_inA__sum'] + \
            World.objects.aggregate(Sum('battleship_inB'))['battleship_inB__sum'] + \
            World.objects.aggregate(Sum('battleship_inC'))['battleship_inC__sum'] + \
            World.objects.aggregate(Sum('battleship_inD'))['battleship_inD__sum'] + \
            World.objects.aggregate(Sum('battleship_inS'))['battleship_inS__sum'] + \
            World.objects.aggregate(Sum('battleship_inH'))['battleship_inH__sum']
        totdre = World.objects.aggregate(Sum('dreadnought_inA'))['dreadnought_inA__sum'] + \
            World.objects.aggregate(Sum('dreadnought_inB'))['dreadnought_inB__sum'] + \
            World.objects.aggregate(Sum('dreadnought_inC'))['dreadnought_inC__sum'] + \
            World.objects.aggregate(Sum('dreadnought_inD'))['dreadnought_inD__sum'] + \
            World.objects.aggregate(Sum('dreadnought_inS'))['dreadnought_inS__sum'] + \
            World.objects.aggregate(Sum('dreadnought_inH'))['dreadnought_inH__sum']
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
    winnerid = data.lotterywinnerid
    winner = (None if winnerid == 0 else World.objects.get(worldid=winnerid))
    prevprize = data.lotterywinneramount

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
        'rsowners':rsowners, 'rumsoddium':rumsoddium, 'jackpot':jackpot, 'winner':winner, 'timeremaining':timeremaining, 'counttext':counttext,
        'prevprize':prevprize, 'rsamount':rsamount, 'stats':stats})


@login_required
@world_required
def tasks(request, world):
    'View and revoke tasks here.'

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
def communiques(request, world):
    'View/delete comms here.'

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
            worldid = form["target"]
            try:
                target = World.objects.get(worldid=worldid)
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
            if not comm.seen and comm.sender.world_name not in unreadlist:
                unreadlist.append(comm.sender.world_name)
        for name in commsdict:
            numberlist.append(len(commsdict[name]))
        if len(commslist) == 0:   # Displays 'no comms'
            commsdict = None

        for name in unreadlist:
            unreadstring += name + ','

        return render(request, 'communiques.html', {'commsdict':commsdict,'numberlist':numberlist,'unread':unreadstring, 'deleteform':deleteform})


@login_required
@world_required
def sentcomms(request, world):
    'View/delete sent comms here.'

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
            worldid = form["target"]
            try:
                target = World.objects.get(worldid=worldid)
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
def newtrade(request, world):
    'Propose a new trade here.'

    message = warprotection = indefwar = None

    if world.wardefender.count() > 0:
        indefwar = True

    if world.gdp < 250:
        return redirect('trades')

    if request.method == 'POST':
        form = NewTradeForm(world.millevel, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            resoffin = data['offer']
            amountoffin = int(data['amountoff'])
            resrecin = data['receive']
            amountrecin = int(data['amountrec'])
            amounttrades = int(data['amounttrades'])
            amountcheck = utilities.tradeamount(world, resoffin, amountoffin*amounttrades)
            shipsendcheck = utilities.tradeshiptech(world, resoffin)
            shipreccheck = utilities.tradeshiptech(world, resrecin)
            shippowercheck = utilities.tradeshippower(world, resoffin, amountoffin*amounttrades)
            defwarcheck = utilities.shippowerdefwars(world, resoffin)
            if (resoffin not in v.resources) or (resrecin not in v.resources):
                message = 'Enter valid resources.'
            elif amountoffin <= 0 or amountrecin <= 0 or amounttrades <= 0:
                message = 'Enter positive numbers.'
            elif resoffin == resrecin:
                message = 'You cannot offer a trade with identical resources!'
            elif amounttrades > 100:
                message = 'You cannot have so many of that trade at once!'
            elif amountcheck is not True:
                message = amountcheck
            elif shipsendcheck is not True:
                message = shipsendcheck
            elif shipreccheck is not True:
                message = shipsendcheck
            elif shippowercheck is not True:
                message = shippowercheck
            elif defwarcheck is not True:
                message = defwarcheck
            elif int(Trade.objects.filter(owner=world).count()) > 10:
                message = 'You have too many trades on the market already!'
            else:
                if 11 <= resoffin <= 19:
                    tempmsg = 'Trade posted.'
                    if v.now() < world.warprotection:
                        world.warprotection = v.now()
                        world.noobprotect = False
                        world.save(update_fields=['warprotection','noobprotect'])
                        tempmsg += '<br>Your war protection is now over.'
                    if indefwar:
                        utilities.contentmentchange(world, -10)
                        utilities.stabilitychange(world, -5)
                        tempmsg += '<br>You have lost perception and stability.'
                    world.tempmsg = tempmsg
                    world.save(update_fields=['tempmsg'])

                Trade.objects.create(owner=world, resoff=resoffin, amountoff=amountoffin, resrec=resrecin,
                    amountrec=amountrecin, amounttrades=amounttrades)
                return redirect('trades')
    else:
        form = NewTradeForm(world.millevel)

    if v.now() < world.warprotection:
        warprotection = True

    if world.econsystem == 1:
        cost = 10
    elif world.econsystem == 0:
        cost = 15
    elif world.econsystem == -1:
        cost = 20

    return render(request, 'newtrade.html', {'form': form, 'cost':cost, 'message':message, 'warprotection':warprotection, 'indefwar':indefwar})


@login_required
@world_required
def trades(request, world):
    'Accept/delete/modify a trade here.'

    warprotection = indefwar = None
    endprotect = ''
    message = world.tempmsg
    if world.tempmsg != None:
        world.tempmsg = None
        world.save(update_fields=['tempmsg'])

    if request.method == 'POST':
        form = request.POST

        if "newtrade" in form:
            if world.gdp < 250:
                message = 'Your economy is too weak for trade! You must have a GDP of 250 million to participate in the galactic market.'
            else:
                return redirect('newtrade')

        if "delete" in form:
            tradeid = request.POST.get('tradeid')
            try:
                trade = Trade.objects.get(pk=int(tradeid))
            except ObjectDoesNotExist:
                pass
            else:
                if trade.owner == world:
                    trade.delete()

        if "modify" in form:
            tradeid = request.POST.get('tradeid')
            tradeno = request.POST.get('tradeno')
            try:
                trade = Trade.objects.get(pk=int(tradeid))
            except ObjectDoesNotExist:
                pass
            else:
                if trade.owner == world:
                    if not utilities.checkno(tradeno):
                        message = 'Enter a positive number.'
                    else:
                        tradeno = int(tradeno)
                        amountcheck = utilities.tradeamount(world, trade.resoff, trade.amountoff*tradeno)
                        shippowercheck = utilities.tradeshippower(world, trade.resoff, trade.amountoff*tradeno)
                        if amountcheck != True:
                            message = amountcheck
                        elif shippowercheck != True:
                            message = shippowercheck
                        elif tradeno > 100:
                            message = 'You cannot have so many of a trade at once!'
                        else:
                            trade.amounttrades = tradeno
                            trade.save()
                            message = 'Trade modified.'
                            if 11 <= trade.resoff <= 19:
                                if v.now() < world.warprotection:
                                    world.warprotection = v.now()
                                    world.noobprotect = False
                                    world.save(update_fields=['warprotection','noobprotect'])
                                    message += '<br>Your war protection is now over.'
                                if indefwar:
                                    utilities.contentmentchange(world, -10)
                                    utilities.stabilitychange(world, -5)
                                    message += '<br>You have lost perception and stability.'

        if "accepttrade" in form:
            tradeid = request.POST.get('tradeid')
            tradeno = request.POST.get('tradeno')
            try:
                trade = Trade.objects.get(pk=int(tradeid))
            except ObjectDoesNotExist:
                message = 'This trade is no longer available!'
            else:
                if not utilities.checkno(tradeno):
                    message = 'Enter a positive number.'
                elif trade.owner == world:
                    message = 'You cannot accept your own trade!'
                else:
                    tradeno = int(tradeno)
                    amountrec = trade.amountrec*tradeno
                    amountoff = trade.amountoff*tradeno
                    amountcheck = utilities.tradeamount(world, trade.resrec, amountrec)
                    otheramountcheck = utilities.tradeamount(trade.owner, trade.resoff, amountoff)
                    othertradecost = utilities.tradecost(trade.owner, tradeno)
                    shipsendcheck = utilities.tradeshiptech(world, trade.resrec)
                    shipreccheck = utilities.tradeshiptech(world, trade.resoff)
                    shippowercheck = utilities.tradeshippower(world, trade.resrec, amountrec)
                    count, countcheck = utilities.freightertradecheck(world, trade.resrec, amountrec)
                    othercount, othercountcheck = utilities.freightertradecheck(trade.owner, trade.resoff, amountoff)
                    offername = utilities.resname(trade.resoff, 2, lower=True)

                    if tradeno > trade.amounttrades:
                        message = 'There is not enough of that trade remaining!'
                    elif amountcheck != True:
                        message = amountcheck
                    elif shipreccheck != True:
                        message = shipreccheck
                    elif shipsendcheck != True:
                        message = shipsendcheck
                    elif shippowercheck != True:
                        message = shippowercheck
                    elif countcheck != True:
                        message = countcheck
                    elif otheramountcheck != True or othertradecost != True:
                        message = 'The world offering this trade cannot uphold it! It has been fined 20%% of its budget.'
                        trade.owner.budget = F('budget') - trade.owner.budget/5
                        trade.owner.save(update_fields=['budget'])

                        reason = ('you did not have enough GEU to pay the upfront cost' if othertradecost != True else offername)
                        htmldata = news.tradefail(reason)
                        NewsItem.objects.create(target=trade.owner, content=htmldata)
                        trade.delete()

                    elif othercountcheck != True:
                        message = 'The world offering this trade does not have the freighters to transport it! It has been fined 20%% of its budget.'
                        trade.owner.budget = F('budget') - trade.owner.budget/5
                        trade.owner.save(update_fields=['budget'])

                        htmldata = news.tradefailfreighters(offername)
                        NewsItem.objects.create(target=trade.owner, content=htmldata)
                        trade.delete()

                    else:
                        if trade.resoff == 0:
                            trainingchange = 0
                            utilities.resourcecompletion(world, trade.resoff, amountoff, trainingchange)
                            utilities.spyintercept(world, trade.owner, 'GEU', amountoff)

                            ResourceLog.objects.create(owner=world, target=trade.owner, res=trade.resoff, amount=amountoff, sent=False, trade=True)

                        elif 11 <= trade.resoff <= 19:
                            delay = (4 if world.region == trade.owner.region else 8)
                            outcometime = v.now() + time.timedelta(hours=delay)
                            if 'sendhome' in world.shipsortprefs:
                                trainingchange = utilities.trainingchangecalc(trade.owner, trade.owner.region, int(trade.resoff)-10, amountoff)
                            else:
                                trainingchange = utilities.trainingchangecalc(trade.owner, 'S', int(trade.resoff)-10, amountoff)

                            taskdetails = taskdata.tradeaccepterarrival(trade.owner, trade.displayoff, amountoff)
                            task = Task(target=world, content=taskdetails, datetime=outcometime)
                            task.save()

                            newtask.tradecomplete.apply_async(args=(trade.owner.worldid, world.worldid, task.pk, trade.resoff, amountoff,
                                trainingchange, 0), eta=outcometime)

                        else:
                            delay = (1 if world.region == trade.owner.region else 2)
                            outcometime = v.now() + time.timedelta(hours=delay)
                            trainingchange = 0

                            trade.owner.freightersinuse = F('freightersinuse') + othercount
                            trade.owner.save(update_fields=['freightersinuse'])

                            taskdetails = taskdata.tradeaccepterarrival(trade.owner, trade.displayoff, amountoff)
                            task = Task(target=world, content=taskdetails, datetime=outcometime)
                            task.save()

                            newtask.tradecomplete.apply_async(args=(trade.owner.worldid, world.worldid, task.pk, trade.resoff, amountoff,
                                trainingchange, othercount), eta=outcometime)

                        utilities.resourcecompletion(trade.owner, trade.resoff, -amountoff, -trainingchange)
                        utilities.freightermove(trade.owner, trade.owner.region, -othercount)
                        utilities.spyinterceptsend(trade.owner, world, trade.displayoff, amountoff)
                        ResourceLog.objects.create(owner=trade.owner, target=world, res=trade.resoff, amount=amountoff, sent=True, trade=True)

                        ##
                        if trade.resrec == 0:
                            trainingchange = 0

                            htmldata = news.tradeacceptmoney(world, trade.displayoff, amountoff, trade.displayrec, amountrec)
                            NewsItem.objects.create(target=trade.owner, content=htmldata)

                            utilities.resourcecompletion(trade.owner, trade.resrec, amountrec, trainingchange)
                            utilities.spyintercept(trade.owner, world, 'GEU', amountrec)

                            ResourceLog.objects.create(owner=trade.owner, target=world, res=trade.resrec, amount=amountrec, sent=False, trade=True)

                        elif 11 <= trade.resrec <= 19:
                            delay = (4 if world.region == trade.owner.region else 8)
                            if v.now() < world.warprotection:
                                world.warprotection = v.now()
                                world.save()
                                endprotect = ' Your war protection is now over. Other worlds may attack you.'
                            outcometime = v.now() + time.timedelta(hours=delay)
                            if 'sendhome' in world.shipsortprefs:
                                trainingchange = utilities.trainingchangecalc(world, world.region, int(trade.resrec)-10, amountrec)
                            else:
                                trainingchange = utilities.trainingchangecalc(world, 'S', int(trade.resrec)-10, amountrec)

                            taskdetails = taskdata.tradeownerarrival(world, trade.displayrec, amountrec)
                            task = Task(target=trade.owner, content=taskdetails, datetime=outcometime)
                            task.save()

                            htmldata = news.tradeaccept(world, trade.displayoff, amountoff, trade.displayrec, amountrec)
                            NewsItem.objects.create(target=trade.owner, content=htmldata)

                            newtask.tradecomplete.apply_async(args=(world.worldid, trade.owner.worldid, task.pk, trade.resrec, amountrec,
                                trainingchange, 0), eta=outcometime)

                        else:
                            delay = (1 if world.region == trade.owner.region else 2)
                            outcometime = v.now() + time.timedelta(hours=delay)
                            trainingchange = 0

                            world.freightersinuse = F('freightersinuse') + count
                            world.save(update_fields=['freightersinuse'])

                            taskdetails = taskdata.tradeownerarrival(world, trade.displayrec, amountrec)
                            task = Task(target=trade.owner, content=taskdetails, datetime=outcometime)
                            task.save()

                            htmldata = news.tradeaccept(world, trade.displayoff, amountoff, trade.displayrec, amountrec)
                            NewsItem.objects.create(target=trade.owner, content=htmldata)

                            newtask.tradecomplete.apply_async(args=(world.worldid, trade.owner.worldid, task.pk, trade.resrec, amountrec,
                                trainingchange, count), eta=outcometime)

                        utilities.resourcecompletion(world, trade.resrec, -amountrec, -trainingchange)
                        utilities.freightermove(world, world.region, -count)
                        utilities.spyinterceptsend(world, trade.owner, trade.displayrec, amountrec)
                        ResourceLog.objects.create(owner=world, target=trade.owner, res=trade.resrec, amount=amountrec, sent=True, trade=True)

                        ##
                        tradelogger.info('---')
                        tradelogger.info('%s (id=%s) accepted trade with %s (id=%s),',
                            world.world_name, world.worldid, trade.owner.world_name, trade.owner.worldid)
                        tradelogger.info('sending %s %s and receiving %s %s',
                            amountrec, trade.displayrec, amountoff, trade.displayoff)

                        if tradeno < trade.amounttrades:
                            trade.amounttrades = F('amounttrades') - tradeno
                            trade.save(update_fields=['amounttrades'])
                        else:
                            trade.delete()

                        message = 'Trade accepted!' + endprotect

    owntradeslist = list(Trade.objects.filter(owner=world).order_by('-datetime'))

    tradeslist = [list(Trade.objects.filter(resoff=0).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=1).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=2).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=3).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=4).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=11).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=12).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=13).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=14).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=15).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=16).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=17).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=18).exclude(owner=world).order_by('-datetime')),
                  list(Trade.objects.filter(resoff=19).exclude(owner=world).order_by('-datetime'))]


    tradenames = ['Currency', 'Warpfuel', 'Duranium', 'Tritanium', 'Adamantium', 'Fighters', 'Corvettes', 'Light Cruisers', 'Destroyers',
                  'Frigates', 'Heavy Cruisers', 'Battlecruisers', 'Battleships', 'Dreadnoughts']

    tot = 0
    for listindex, tradelist in enumerate(tradeslist):
        if not tradelist:
            tradeslist[listindex] = None
            tot += 1
        else:
            for index, trade in enumerate(tradelist):
                if trade.resoff == 0:
                    delay = None
                elif 11 <= trade.resoff <= 19:
                    delay = (4 if world.region == trade.owner.region else 8)
                else:
                    delay = (1 if world.region == trade.owner.region else 2)
                tradeslist[listindex][index] = {'info':trade,'delay':delay}

    notrades = (True if tot == len(tradeslist) else False)

    warprotection = (True if v.now() < world.warprotection else False)

    if not owntradeslist:
        owntradeslist = False

    indefwar = (True if world.wardefender.count() else False)

    world = World.objects.get(pk=world.pk)
    reslist = [world.budget, world.warpfuel, world.duranium, world.tritanium, world.adamantium]

    return render(request, 'trades.html', {'owntrades':owntradeslist, 'message':message, 'warprotection':warprotection, 'notrades': notrades,
        'reslist':reslist, 'indefwar':indefwar, 'tradeslist':tradeslist, 'tradenames':tradenames})


def stats(request):
    'Base stats page, redirects to 1st stats page'
    return redirect('statspage', 1)


def statspage(request, page):
    'Stats page, displays 20 worlds at a time. Searches by name'
    results = showform = world = None
    flagpref = 'new'
    displayno = 20

    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        showform = None
        sortform = GalaxySortForm()
        sort = 'worldid'
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
            results = World.objects.filter(world_name__icontains=searchdata).exclude(pk=0)
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

    if World.objects.filter(worldid=request.user.id).exists():
        sortform = GalaxySortForm(initial={'sortby':world.galaxysort})
    else:
        sortform = GalaxySortForm()

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
        world = World.objects.get(worldid=request.user.id)
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

        world = World.objects.get(pk=world.pk)

    alliance, alliancemembs, officers, leader = utilities.alliancedata(request, allid)

    return render(request, 'alliances_ind.html', {'world': world, 'alliance': alliance,'leader': leader,
                                                  'officers': officers,'alliancemembs': alliancemembs,
                                                  'message': message, 'displayentry': displayentry,'leave':leave})


@login_required
@world_required
def alliances_logs(request, allid, world):
    'Displays alliance logs. Only leaders and officers allowed.'

    alliance = Alliance.objects.get(allianceid=allid)

    if not (world.alliance == alliance and (world.officer or world.leader)):
        return redirect('main')
    else:
        loglist = list(BankLog.objects.filter(alliance=alliance).order_by('-datetime'))
        return render(request, 'alliances_logs.html', {'alliance':alliance,'loglist': loglist})


@login_required
@world_required
def alliances_memberlogs(request, allid, world):
    'Displays member logs. Only leaders and officers allowed.'

    alliance = Alliance.objects.get(allianceid=allid)

    if not (world.alliance == alliance and (world.officer or world.leader)):
        return redirect('main')
    else:
        loglist = list(AllianceLog.objects.filter(alliance=alliance).order_by('-datetime'))
        return render(request, 'alliances_memberlogs.html', {'alliance':alliance,'loglist': loglist})


@login_required
@world_required
def alliances_admin(request, allid, world):
    'Admin an alliance here. Only leaders and officers allowed, with different functions.'

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
                    successor = World.objects.get(world_name=name)
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
                    invitee = World.objects.get(world_name=name)
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
def alliances_stats(request, allid, world):
    'Displays stats of an alliance.'

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
    totA = alliance.allmember.all().filter(region='A').count()
    totB = alliance.allmember.all().filter(region='B').count()
    totC = alliance.allmember.all().filter(region='C').count()
    totD = alliance.allmember.all().filter(region='D').count()
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
    totfreighters = alliance.allmember.all().aggregate(Sum('freighters'))['freighters__sum']
    totshipyards = alliance.allmember.all().aggregate(Sum('shipyards'))['shipyards__sum']
    totfig = alliance.allmember.all().aggregate(Sum('fighters_inA'))['fighters_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('fighters_inB'))['fighters_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('fighters_inC'))['fighters_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('fighters_inD'))['fighters_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('fighters_inS'))['fighters_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('fighters_inH'))['fighters_inH__sum']
    totcor = alliance.allmember.all().aggregate(Sum('corvette_inA'))['corvette_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('corvette_inB'))['corvette_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('corvette_inC'))['corvette_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('corvette_inD'))['corvette_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('corvette_inS'))['corvette_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('corvette_inH'))['corvette_inH__sum']
    totlcr = alliance.allmember.all().aggregate(Sum('light_cruiser_inA'))['light_cruiser_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('light_cruiser_inB'))['light_cruiser_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('light_cruiser_inC'))['light_cruiser_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('light_cruiser_inD'))['light_cruiser_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('light_cruiser_inS'))['light_cruiser_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('light_cruiser_inH'))['light_cruiser_inH__sum']
    totdes = alliance.allmember.all().aggregate(Sum('destroyer_inA'))['destroyer_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('destroyer_inB'))['destroyer_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('destroyer_inC'))['destroyer_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('destroyer_inD'))['destroyer_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('destroyer_inS'))['destroyer_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('destroyer_inH'))['destroyer_inH__sum']
    totfri = alliance.allmember.all().aggregate(Sum('frigate_inA'))['frigate_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('frigate_inB'))['frigate_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('frigate_inC'))['frigate_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('frigate_inD'))['frigate_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('frigate_inS'))['frigate_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('frigate_inH'))['frigate_inH__sum']
    tothcr = alliance.allmember.all().aggregate(Sum('heavy_cruiser_inA'))['heavy_cruiser_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('heavy_cruiser_inB'))['heavy_cruiser_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('heavy_cruiser_inC'))['heavy_cruiser_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('heavy_cruiser_inD'))['heavy_cruiser_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('heavy_cruiser_inS'))['heavy_cruiser_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('heavy_cruiser_inH'))['heavy_cruiser_inH__sum']
    totbcr = alliance.allmember.all().aggregate(Sum('battlecruiser_inA'))['battlecruiser_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('battlecruiser_inB'))['battlecruiser_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('battlecruiser_inC'))['battlecruiser_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('battlecruiser_inD'))['battlecruiser_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('battlecruiser_inS'))['battlecruiser_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('battlecruiser_inH'))['battlecruiser_inH__sum']
    totbsh = alliance.allmember.all().aggregate(Sum('battleship_inA'))['battleship_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('battleship_inB'))['battleship_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('battleship_inC'))['battleship_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('battleship_inD'))['battleship_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('battleship_inS'))['battleship_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('battleship_inH'))['battleship_inH__sum']
    totdre = alliance.allmember.all().aggregate(Sum('dreadnought_inA'))['dreadnought_inA__sum'] + \
        alliance.allmember.all().aggregate(Sum('dreadnought_inB'))['dreadnought_inB__sum'] + \
        alliance.allmember.all().aggregate(Sum('dreadnought_inC'))['dreadnought_inC__sum'] + \
        alliance.allmember.all().aggregate(Sum('dreadnought_inD'))['dreadnought_inD__sum'] + \
        alliance.allmember.all().aggregate(Sum('dreadnought_inS'))['dreadnought_inS__sum'] + \
        alliance.allmember.all().aggregate(Sum('dreadnought_inH'))['dreadnought_inH__sum']
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
def new_alliance(request, world):
    'New alliance page, checks if the world has not got an alliance and if fee to create paid.'

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


#GDP Sales stuff
@login_required
@world_required
def gdphome(request, world):
    'GDP Offers Home View'

    message = None
    try:
        youroffer = GDPSale.objects.get(seller=world)
    except GDPSale.DoesNotExist:
        youroffer = None
    return render(request, 'gdpsale/gdphome.html', {'message':message, 'youroffer':youroffer})


@login_required
@world_required
def gdpoffers(request, world):
    'View for GDP Offers list'

    message = None
    offers = GDPSale.objects.filter(buyer=world)
    return render(request, 'gdpsale/gdpoffers.html', {'message': message, 'offers': offers, })


@login_required
@world_required
def gdpmakeoffer(request, world):
    'Return POST data or view for making gdp offers'

    if request.method == 'POST':
        form = GDPSaleForm(request.POST)
        if form.is_valid():
            buyer = form.cleaned_data['buyer']
            buyer = World.objects.get(worldid=buyer)
            if buyer == world:
                message = "You cannot offer yourself!"
                return render(request, 'gdpsale/gdphome.html', {'message': message})
            #CHECK FOR EXISTING SALE
            try:
                salecheck = GDPSale.objects.get(seller=world)
                message = "You already have a pending sale!"
                return render(request, 'gdpsale/gdphome.html', {'message': message})
            #ENDCHECK
            except GDPSale.DoesNotExist:
                try:
                    threshold = GDPSaleThresholdManager.objects.get(target=world)
                except GDPSaleThresholdManager.DoesNotExist:
                    threshold = GDPSaleThresholdManager(target=world, sellthreshold=world.gdp*0.25, buythreshold=world.gdp*0.5)
                    threshold.save()
                threshold = GDPSaleThresholdManager.objects.get(target=world)
                geuamount = form.cleaned_data['geuamount']
                gdpamount = form.cleaned_data['gdpamount']

                #Check GDP in Seller's World
                if gdpamount > world.gdp:
                    message = "You do not have enough GDP to sell that much!"
                    return render(request, 'gdpsale/gdphome.html', {'message': message})
                if gdpamount > threshold.sellthreshold:
                    message = "You are attempting to sell too much GDP this turn!"
                    return render(request, 'gdpsale/gdphome.html', {'message': message})

            sale = GDPSale(seller=world, buyer=buyer, gdpamount=gdpamount, geuamount=geuamount)
            sale.save()
            message = "Offer Successfully Sent!"
            return render(request, 'gdpsale/gdphome.html', {'message': message})

        return render(request, 'gdpsale/gdpmakeoffer.html', {'form': form})

    message = None

    form = GDPSaleForm()

    return render(request, 'gdpsale/gdpmakeoffer.html', {'form': form})


@login_required
@world_required
def acceptgdpsale(request, saleid, world):
    'Process acceptance of GDP Sale'

    message = None
    sale = get_object_or_404(GDPSale, id=saleid)
    seller = sale.seller
    thresholdbuyer = GDPSaleThresholdManager.objects.get(target=world)
    thresholdseller = GDPSaleThresholdManager.objects.get(target=seller)

    #world is equal to the buyer
    if sale.buyer != world:
        #Verify sale belongs to user
        return redirect("gdphome")
    #Verify Buy Threshold for Buyer
    elif sale.gdpamount > thresholdbuyer.buythreshold:
        message = "You are attempting to buy too much GDP this turn!"
        return render(request, 'gdpsale/gdphome.html', {'message': message})
    #Verify Sell Threshold for Seller Again
    elif sale.gdpamount > thresholdseller.sellthreshold:
        message = "The seller has sold too much of his GDP this turn! This offer will be automatically cancelled!"
        sale.delete()
        return render(request, 'gdpsale/gdphome.html', {'message': message})
    else:
        #Checks done, running sale process!
        seller.gdp = seller.gdp - sale.gdpamount
        seller.budget = seller.budget + sale.geuamount
        seller.save()
        world.gdp = world.gdp + sale.gdpamount
        world.budget = world.budget - sale.geuamount
        world.save()
        thresholdseller.sellthreshold = thresholdseller.sellthreshold - sale.gdpamount
        thresholdbuyer.buythreshold = thresholdbuyer.buythreshold - sale.gdpamount
        thresholdseller.save()
        thresholdbuyer.save()
        sale.delete()
        message = "GDP Sale Offer Accepted!"
        return render(request, 'gdpsale/gdphome.html', {'message': message})


@login_required
@world_required
def denygdpsale(request, saleid, world):
    'Process denial of GDP Sale'

    message = None
    #World is equal to the buyer
    sale = get_object_or_404(GDPSale, id=saleid)
    #Verify sale belongs to user
    if sale.buyer != world:
        return redirect("gdphome")
    else:
        seller = sale.seller
        seller = seller.world_name
        sale.delete()
        message = "You have rejected %s's GDP Sale offer!" % seller
        return render(request, 'gdpsale/gdphome.html', {'message': message})


@login_required
@world_required
def revokegdpsale(request, saleid, world):
    'Process revocation of GDP Sale'

    message = None
    sale = get_object_or_404(GDPSale, id=saleid)
    if sale.seller != world:
        return redirect("gdphome")
    else:
        buyer = sale.buyer
        buyer = buyer.world_name
        sale.delete()
        message = "You have revoked your GDP Sale offer with %s!" % buyer
        return render(request, 'gdpsale/gdphome.html', {'message': message})
