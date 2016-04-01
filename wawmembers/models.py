# Django Imports
from django.db import models
from django.core.cache import cache

# Python Imports
import decimal

# WaW Imports
import wawmembers.variables as v

'''
All objects live here. This is the interface between Python and database data.
'''

# most of these should be positive integer fields


D = decimal.Decimal

class NotVacation(models.Manager):
    def get_queryset(self):
        return super(NotVacation, self).get_queryset().filter(vacation=False)


class World(models.Model):
    # Meta
    worldid = models.IntegerField(default=0, unique=True, verbose_name="world ID",
                            help_text="Don't change this.", primary_key=True)
    donator = models.BooleanField(default=False)
    world_descriptor = models.CharField(max_length=100, default='The World of', verbose_name="world title")
    leadertitle = models.CharField(max_length=100, default='Leader', verbose_name="leader title")
    user_name = models.CharField(max_length=30, unique=True, verbose_name="username")

    world_name = models.CharField(max_length=20, unique=True)
    world_desc = models.TextField(max_length=500, blank=True,
        default='Welcome to Worlds at War! [br] Go to the settings page to change this description!')

    creationtime = models.DateTimeField(default=v.now, verbose_name="creation time")
    lastloggedintime = models.DateTimeField(default=v.now, verbose_name="last logged in time")

    creationip = models.IPAddressField(default='127.0.0.1', verbose_name="creation IP")
    lastloggedinip = models.IPAddressField(default='127.0.0.1', verbose_name="last logged in IP")

    region = models.CharField(max_length=1, help_text="A: Amyntas, B: Bion, C: Cleon, D: Draco", default='A')

    vacation = models.BooleanField(default=False)

    tempmsg = models.CharField(max_length=200, null=True, default=None)

    avatar = models.CharField(max_length=4,default='av01')
    flag = models.CharField(max_length=4,default='fl02')

    donatoravatar = models.CharField(max_length=200, default='https://wawgame.eu/static/avatarsnflags/av01.gif')
    donatorflag = models.CharField(max_length=200, default='https://wawgame.eu/static/avatarsnflags/fl02.gif')
    donatoranthem = models.CharField(max_length=200, default='jIxas0a-KgM')

    card = models.CharField(max_length=100, default='None')

    galaxysort = models.CharField(max_length=200, default='worldid')
    commpref = models.CharField(max_length=10, default='new')
    flagpref = models.CharField(max_length=10, default='new')
    worlddisplayno = models.IntegerField(default=20)
    statsopenprefs = models.CharField(max_length=50, default='domestic,economic,diplomacy,military')
    backgroundpref = models.IntegerField(default=-1)
    policypref = models.CharField(max_length=10, default='js')
    buildpref = models.CharField(max_length=5, default='multi')

    objects = models.Manager()
    not_vacation_objects = NotVacation()

    # Economy
    econsystem = models.IntegerField(verbose_name="economics System", default=0,
        help_text="-1: Central Planning. 0: Mixed Economy. 1: Free Market.")

    gdp = models.IntegerField(default=500, help_text="million GEU")
    budget = models.DecimalField(default=2000, max_digits=18, decimal_places=1, help_text="GEU")
    growth = models.IntegerField(default=2, help_text="million GEU")
    industrialprogram = models.IntegerField(default=0)

    econchanged = models.BooleanField(default=False)
    resource = models.IntegerField(default=1)

    def _res_display(self):
        from wawmembers.utilities import trade_display
        return trade_display(self.resource)
    displayresource = property(_res_display)

    def _res_prod(self):
        return Agreement.objects.filter(sender=self).count()
    resourceproduction = property(_res_prod)

    rumsoddium = models.IntegerField(default=0)

    # Domestic
    polsystem = models.IntegerField(verbose_name="political System", default=0,
        help_text="""
        -100 to -60: Autocracy. -59 to -19: Fleet Admiralty. -20 to 20: Single-party Rule.
        21 to 59: Totalitarian Democracy. 60 to 100: Liberal Democracy.
        """)

    contentment = models.IntegerField(default=0,
        help_text="""
        -100 to -81: Planetary enemy. -80 to -61: Despised. -60 to -41: Hated.
        -40 to -21: Disliked. -20 to -1: Middling. <br> 0 to 19: Decent. 20 to 39: Liked.
        40 to 59: Loved. 60 to 79: Planetary hero. 80 to 100: God amongst men.
        """)

    stability = models.IntegerField(default=0,
        help_text="""
        -100 to -81: Anarchy. -80 to -61: Brink of Collapse. -60 to -41: Chaotic.
        -40 to -21: Rioting. -20 to -1: Growing Tensions. <br> 0 to 19: Manageable. 20 to 39: Ticking over.
        40 to 59: Efficient. 60 to 79: Pillar of society. 80 to 100: Unsinkable.
        """)

    qol = models.IntegerField(default=0,
        help_text="""
        -100 to -81: Wasteland. -80 to -61: Edge of collapse. -60 to -41: Abject misery.
        -40 to -21: Disdvantaged. -20 to -1: Average. <br> 0 to 19: Reasonable. 20 to 39: Decent.
        40 to 59: Civilised. 60 to 79: Sophisticated. 80 to 100: Utopia.
        """)

    rebels = models.IntegerField(default=0,
        help_text="""
        0: None. 1 to 19: Scattered Fighters. 20 to 39: Organised Squadrons.
        40 to 59: Tenacious Guerrillas. <br> 60 to 79: Open Rebellion. 80 to 100: System-wide War.
        """)

    # Materials
    warpfuel = models.IntegerField(default=10)
    warpfuelprod = models.IntegerField(default=10)
    duranium = models.IntegerField(default=10)
    duraniumprod = models.IntegerField(default=3)
    tritanium = models.IntegerField(default=0)
    tritaniumprod = models.IntegerField(default=0)
    adamantium = models.IntegerField(default=0)
    adamantiumprod = models.IntegerField(default=0)

    freighters = models.IntegerField(default=5)
    freightersinuse = models.IntegerField(default=0)

    freighter_inA = models.IntegerField(default=0, verbose_name="A freighters")
    freighter_inB = models.IntegerField(default=0, verbose_name="B freighters")
    freighter_inC = models.IntegerField(default=0, verbose_name="C freighters")
    freighter_inD = models.IntegerField(default=0, verbose_name="D freighters")
    freighter_inS = models.IntegerField(default=0, verbose_name="S freighters")

    salvdur = models.IntegerField(default=0, verbose_name="salvage duranium")
    salvtrit = models.IntegerField(default=0, verbose_name="salvage tritanium")
    salvadam = models.IntegerField(default=0, verbose_name="salvage adamantium")
    turnsalvaged = models.BooleanField(default=False)

    # General Military
    millevel = models.IntegerField(default=0, verbose_name="military Level")
    turnresearched = models.BooleanField(default=False)
    warpoints = models.IntegerField(default=0)

    timetonextadmiralty = models.DateTimeField(default=v.now, verbose_name="next admiralty")

    startpower = models.IntegerField(default=0, verbose_name="power at turn start")
    powersent = models.IntegerField(default=0, verbose_name="power sent")

    warsperturn = models.IntegerField(default=0)
    declaredwars = models.ManyToManyField('World', related_name='declaredwars+', default=None, blank=True)
    noobprotect = models.BooleanField(default=True)

    warprotection = models.DateTimeField(default=v.nowplusweek, verbose_name="war protection")
    abovegdpprotection = models.DateTimeField(default=v.now, verbose_name="higher-gdp protection")
    brokenwarprotect = models.DateTimeField(default=v.now, verbose_name="time till able to get protection")

    shipyards = models.IntegerField(default=10)
    shipyardsinuse = models.IntegerField(default=0)

    shipsortprefs = models.CharField(max_length=50, default='prodhome,sendhome,receivehome')

    flagshiptype = models.IntegerField(default=0,
        help_text="""
        0: No Flagship, 1: Personal Fighter, 2: Militarised Yacht, 3: Command Ship
        """)
    flagshipbuild = models.BooleanField(default=False)
    flagshiplocation = models.CharField(max_length=1, help_text="A: Amyntas, B: Bion, C: Cleon, D: Draco", default='A')
    flagshipname = models.CharField(max_length=30, default='Executor')
    flagshippicture = models.CharField(max_length=4,default='pf01')
    donatorflagship = models.CharField(max_length=200, default='http://wawgame.eu/static/personalships/my10.gif')

    # Ships
    fleetname_inA = models.CharField(max_length=15, default='Alpha', verbose_name="A sector name", blank=True)
    fleet_inA_training = models.IntegerField(default=1, verbose_name="A training level")
    fleet_inA_weariness = models.IntegerField(default=200, verbose_name="A weariness")

    fighters_inA = models.IntegerField(default=0, verbose_name="A fighters")
    corvette_inA = models.IntegerField(default=0, verbose_name="A corvettes")
    light_cruiser_inA = models.IntegerField(default=0, verbose_name="A light cruisers")
    destroyer_inA = models.IntegerField(default=0, verbose_name="A destroyers")
    frigate_inA = models.IntegerField(default=0, verbose_name="A frigates")
    heavy_cruiser_inA = models.IntegerField(default=0, verbose_name="A heavy cruisers")
    battlecruiser_inA = models.IntegerField(default=0, verbose_name="A battlecruisers")
    battleship_inA = models.IntegerField(default=0, verbose_name="A battleships")
    dreadnought_inA = models.IntegerField(default=0, verbose_name="A dreadnoughts")

    fleetname_inB = models.CharField(max_length=15, default='Beta', verbose_name="B sector name", blank=True)
    fleet_inB_training = models.IntegerField(default=1, verbose_name="B training level")
    fleet_inB_weariness = models.IntegerField(default=200, verbose_name="B weariness")

    fighters_inB = models.IntegerField(default=0, verbose_name="B fighters")
    corvette_inB = models.IntegerField(default=0, verbose_name="B corvettes")
    light_cruiser_inB = models.IntegerField(default=0, verbose_name="B light cruisers")
    destroyer_inB = models.IntegerField(default=0, verbose_name="B destroyers")
    frigate_inB = models.IntegerField(default=0, verbose_name="B frigates")
    heavy_cruiser_inB = models.IntegerField(default=0, verbose_name="B heavy cruisers")
    battlecruiser_inB = models.IntegerField(default=0, verbose_name="B battlecruisers")
    battleship_inB = models.IntegerField(default=0, verbose_name="B battleships")
    dreadnought_inB = models.IntegerField(default=0, verbose_name="B dreadnoughts")

    fleetname_inC = models.CharField(max_length=15, default='Gamma', verbose_name="C sector name", blank=True)
    fleet_inC_training = models.IntegerField(default=1, verbose_name="C training level")
    fleet_inC_weariness = models.IntegerField(default=200, verbose_name="C weariness")

    fighters_inC = models.IntegerField(default=0, verbose_name="C fighters")
    corvette_inC = models.IntegerField(default=0, verbose_name="C corvettes")
    light_cruiser_inC = models.IntegerField(default=0, verbose_name="C light cruisers")
    destroyer_inC = models.IntegerField(default=0, verbose_name="C destroyers")
    frigate_inC = models.IntegerField(default=0, verbose_name="C frigates")
    heavy_cruiser_inC = models.IntegerField(default=0, verbose_name="C heavy cruisers")
    battlecruiser_inC = models.IntegerField(default=0, verbose_name="C battlecruisers")
    battleship_inC = models.IntegerField(default=0, verbose_name="C battleships")
    dreadnought_inC = models.IntegerField(default=0, verbose_name="C dreadnoughts")

    fleetname_inD = models.CharField(max_length=15, default='Delta', verbose_name="D sector name", blank=True)
    fleet_inD_training = models.IntegerField(default=1, verbose_name="D training level")
    fleet_inD_weariness = models.IntegerField(default=200, verbose_name="D weariness")

    fighters_inD = models.IntegerField(default=0, verbose_name="D fighters")
    corvette_inD = models.IntegerField(default=0, verbose_name="D corvettes")
    light_cruiser_inD = models.IntegerField(default=0, verbose_name="D light cruisers")
    destroyer_inD = models.IntegerField(default=0, verbose_name="D destroyers")
    frigate_inD = models.IntegerField(default=0, verbose_name="D frigates")
    heavy_cruiser_inD = models.IntegerField(default=0, verbose_name="D heavy cruisers")
    battlecruiser_inD = models.IntegerField(default=0, verbose_name="D battlecruisers")
    battleship_inD = models.IntegerField(default=0, verbose_name="D battleships")
    dreadnought_inD = models.IntegerField(default=0, verbose_name="D dreadnoughts")

    fleetname_inH = models.CharField(max_length=15, default='Eta', verbose_name="Hangars name", blank=True)
    fleet_inH_training = models.IntegerField(default=1, verbose_name="H training level")
    fighters_inH = models.IntegerField(default=0, verbose_name="H fighters")
    corvette_inH = models.IntegerField(default=0, verbose_name="H corvettes")
    light_cruiser_inH = models.IntegerField(default=0, verbose_name="H light cruisers")
    destroyer_inH = models.IntegerField(default=0, verbose_name="H destroyers")
    frigate_inH = models.IntegerField(default=0, verbose_name="H frigates")
    heavy_cruiser_inH = models.IntegerField(default=0, verbose_name="H heavy cruisers")
    battlecruiser_inH = models.IntegerField(default=0, verbose_name="H battlecruisers")
    battleship_inH = models.IntegerField(default=0, verbose_name="H battleships")
    dreadnought_inH = models.IntegerField(default=0, verbose_name="H dreadnoughts")

    fleetname_inS = models.CharField(max_length=15, default='Sigma', verbose_name="Staging area name", blank=True)
    fleet_inS_training = models.IntegerField(default=1, verbose_name="S training level")
    fighters_inS = models.IntegerField(default=0, verbose_name="S fighters")
    corvette_inS = models.IntegerField(default=0, verbose_name="S corvettes")
    light_cruiser_inS = models.IntegerField(default=0, verbose_name="S light cruisers")
    destroyer_inS = models.IntegerField(default=0, verbose_name="S destroyers")
    frigate_inS = models.IntegerField(default=0, verbose_name="S frigates")
    heavy_cruiser_inS = models.IntegerField(default=0, verbose_name="S heavy cruisers")
    battlecruiser_inS = models.IntegerField(default=0, verbose_name="S battlecruisers")
    battleship_inS = models.IntegerField(default=0, verbose_name="S battleships")
    dreadnought_inS = models.IntegerField(default=0, verbose_name="S dreadnoughts")

    #Alliance
    alliance = models.ForeignKey('Alliance', related_name='allmember',
        default=None, blank=True, null=True, on_delete=models.SET_NULL)
    alliancepaid = models.BooleanField(default=False)
    officer = models.NullBooleanField(default=False)
    leader = models.NullBooleanField(default=False)

    # Meta
    def __unicode__(self):
        return unicode(self.world_name)

    def _region_display(self):
        if self.region == 'A':
            return 'Amyntas'
        elif self.region == 'B':
            return 'Bion'
        elif self.region == 'C':
            return 'Cleon'
        elif self.region == 'D':
            return 'Draco'
    displayregion = property(_region_display)

    def _pship_display(self):
        if self.flagshiptype == 0:
            return None
        elif self.flagshiptype == 1:
            return 'Personal Fighter'
        elif self.flagshiptype == 2:
            return 'Militarised Yacht'
        elif self.flagshiptype == 3:
            return 'Command Ship'
    displaypship = property(_pship_display)

    def _econ_display(self):
        if self.econsystem == 1:
            return 'Free Market'
        elif self.econsystem == 0:
            return 'Mixed Economy'
        elif self.econsystem == -1:
            return 'Central Planning'
    displayecon = property(_econ_display)

    def _pol_display(self):
        if self.polsystem >= 60:
            return 'Liberal Democracy'
        elif 20 < self.polsystem < 60:
            return 'Totalitarian Democracy'
        elif -20 <= self.polsystem <= 20:
            return 'Single-party Rule'
        elif -60 < self.polsystem < -20:
            return 'Fleet Admiralty'
        elif self.polsystem <= -60:
            return 'Autocracy'
    displaypol = property(_pol_display)

    def _contentment_display(self):
        if self.contentment >= 80:
            return '<i style="color:green;">God amongst men</i>'
        elif 60 <= self.contentment < 80:
            return '<i style="color:green;">Planetary hero</i>'
        elif 40 <= self.contentment < 60:
            return '<i style="color:green;">Loved</i>'
        elif 20 <= self.contentment < 40:
            return '<i>Liked</i>'
        elif 0 <= self.contentment < 20:
            return '<i>Decent</i>'
        elif -20 <= self.contentment < 0:
            return '<i>Middling</i>'
        elif -40 <= self.contentment < -20:
            return '<i>Disliked</i>'
        elif -60 <= self.contentment < -40:
            return '<i style="color:red;">Hated</i>'
        elif -80 <= self.contentment < -60:
            return '<i style="color:red;">Despised</i>'
        elif self.contentment < -80:
            return '<i style="color:red;">Planetary enemy</i>'
    displaycontentment = property(_contentment_display)

    def _stability_display(self):
        if self.stability >= 80:
            return '<i style="color:green;">Unsinkable</i>'
        elif 60 <= self.stability < 80:
            return '<i style="color:green;">Pillar of society</i>'
        elif 40 <= self.stability < 60:
            return '<i style="color:green;">Mostly stable</i>'
        elif 20 <= self.stability < 40:
            return '<i>Ticking over</i>'
        elif 0 <= self.stability < 20:
            return '<i>Manageable</i>'
        elif -20 <= self.stability < 0:
            return '<i>Growing Tensions</i>'
        elif -40 <= self.stability < -20:
            return '<i>Rioting</i>'
        elif -60 <= self.stability < -40:
            return '<i style="color:red;">Chaotic</i>'
        elif -80 <= self.stability < -60:
            return '<i style="color:red;">Brink of Collapse</i>'
        elif self.stability < -80:
            return '<i style="color:red;">Anarchy</i>'
    displaystability = property(_stability_display)

    def _qol_display(self):
        if self.qol >= 80:
            return '<i style="color:green;">Utopia</i>'
        elif 60 <= self.qol < 80:
            return '<i style="color:green;">Sophisticated</i>'
        elif 40 <= self.qol < 60:
            return '<i style="color:green;">Civilised</i>'
        elif 20 <= self.qol < 40:
            return '<i>Decent</i>'
        elif 0 <= self.qol < 20:
            return '<i>Reasonable</i>'
        elif -20 <= self.qol < 0:
            return '<i>Average</i>'
        elif -40 <= self.qol < -20:
            return '<i style="color:red;">Disadvantaged</i>'
        elif -60 <= self.qol < -40:
            return '<i style="color:red;">Abject misery</i>'
        elif -80 <= self.qol < -60:
            return '<i style="color:red;">Edge of collapse</i>'
        elif self.qol < -80:
            return '<i style="color:red;">Wasteland</i>'
    displayqol = property(_qol_display)

    def _rebels_display(self):
        if self.rebels >= 80:
            return '<i style="color:red;">System-wide War</i>'
        elif 60 <= self.rebels < 80:
            return '<i style="color:red;">Open Rebellion</i>'
        elif 40 <= self.rebels < 60:
            return '<i style="color:red;">Tenacious Guerrillas</i>'
        elif 20 <= self.rebels < 40:
            return '<i style="color:red;">Organised Squadrons</i>'
        elif 0 < self.rebels < 20:
            return '<i>Scattered Fighters</i>'
        elif self.rebels == 0:
            return '<i style="color:green;">None</i>'
    displayrebels = property(_rebels_display)

    def _name_display(self):
        return ('<span style=\"color:steelblue;\">%s</span>' % self.user_name if self.donator else self.user_name)
    displayname = property(_name_display)

    def _resource_display(self):
        from wawmembers.display import trade_display
        return trade_display(self.resource)
    displayresource = property(_resource_display)

    def save(self, *args, **kwargs):
        # update world and leader titles
        if not self.donator:
            if self.polsystem >= 60:
                self.leadertitle = 'Prime Minister'
                self.world_descriptor = "The Democratic World of"
            elif 20 < self.polsystem < 60:
                self.leadertitle = 'President'
                self.world_descriptor = "The Technically Democratic World of"
            elif -20 <= self.polsystem <= 20:
                self.leadertitle = 'General Secretary'
                self.world_descriptor = "The People's World of"
            elif -60 < self.polsystem < -20:
                self.leadertitle = 'Lord Admiral'
                self.world_descriptor = "The Grand World of"
            elif self.polsystem <= -60:
                self.leadertitle = 'Beloved Leader'
                self.world_descriptor = "The Supremely Grand Democratic People's World of"
        super(World, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        nullworld = World.objects.get(pk=0)
        # move spies back
        for spy in Spy.objects.filter(location=self):
            data = 'The world your spy was in has been deleted, so your spy has been returned.'
            NewsItem.objects.create(target=spy.owner, content=data)
            spy.locationreset()
        # undo agreements
        for agreement in Agreement.objects.filter(receiver=self):
            agreement.receiver = agreement.sender
            agreement.order = 0
            agreement.save(update_fields=['receiver', 'order'])
        # preserve items
        for comm in Comm.objects.filter(sender=self):
            comm.sender = nullworld
            comm.save(update_fields=['sender'])
        for sentcomm in SentComm.objects.filter(target=self):
            sentcomm.target = nullworld
            sentcomm.save(update_fields=['target'])
        for anno in Announcement.objects.filter(sender=self):
            anno.sender = nullworld
            anno.save(update_fields=['sender'])
        for reslog in ResourceLog.objects.filter(target=self):
            reslog.target = nullworld
            reslog.save(update_fields=['target'])
        for warlog in WarLog.objects.filter(target=self):
            warlog.target = nullworld
            warlog.save(update_fields=['target'])
        for banklog in BankLog.objects.filter(world=self):
            banklog.world = nullworld
            banklog.save(update_fields=['world'])
        for agreementlog in AgreementLog.objects.filter(target=self):
            agreementlog.target = nullworld
            agreementlog.save(update_fields=['target'])
        for alliancelog in AllianceLog.objects.filter(officer=self):
            alliancelog.officer = nullworld
            alliancelog.save(update_fields=['officer'])
        for alliancelog in AllianceLog.objects.filter(world=self):
            alliancelog.world = nullworld
            alliancelog.save(update_fields=['world'])
        super(World, self).delete(*args, **kwargs)


class Alliance(models.Model):
    allianceid = models.AutoField(primary_key=True)
    alliance_name = models.CharField(max_length=20, unique=True)
    alliance_desc = models.TextField(max_length=200, default='Your alliance description goes here.')
    alliance_flag = models.CharField(max_length=200, default='http://www.12manage.com/images/picture_strategic_alliance.jpg')
    alliance_anthem = models.CharField(max_length=200, default='jIxas0a-KgM')
    publicstats = models.CharField(max_length=150, default='', blank=True, null=True)
    memberstats = models.CharField(max_length=150, default='', blank=True, null=True)
    officerstats = models.CharField(max_length=150, default='', blank=True, null=True)
    leaderstats = models.CharField(max_length=150,
        default='leadergeneral,leadereconomic,leaderresources,leadermilitary,leaderecontypes,leaderpoltypes,leadermillevels', null=True)
    bank = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    invites = models.ManyToManyField('World', related_name='allianceinvites', default=None, blank=True)

    def __unicode__(self):
        return unicode(self.alliance_name)


class Spy(models.Model):
    name = models.CharField(max_length=10, default='Name')
    owner = models.ForeignKey('World', related_name='spyowner')
    location = models.ForeignKey('World', related_name='spylocation')
    infiltration = models.IntegerField(default=0)
    propaganda = models.IntegerField(default=0)
    gunrunning = models.IntegerField(default=0)
    intelligence = models.IntegerField(default=0)
    inteltime = models.DateTimeField(default=v.now)
    resinteltime = models.DateTimeField(default=v.now)
    sabotage = models.IntegerField(default=0)
    counterint = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    timespent = models.IntegerField(default=0)
    nextaction = models.DateTimeField(default=v.now)

    def locationreset(self):
        self.location = self.owner
        self.inteltime = v.now()
        self.resinteltime = v.now()
        self.timespent = 0
        self.nextaction = v.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.infiltration > 10:
            self.infiltration = 10
        if self.propaganda > 10:
            self.propaganda = 10
        if self.gunrunning > 10:
            self.gunrunning = 10
        if self.intelligence > 10:
            self.intelligence = 10
        if self.sabotage > 10:
            self.sabotage = 10
        if self.counterint > 10:
            self.counterint = 10
        if self.timespent > 10:
            self.timespent = 10
        self.total = self.infiltration + self.propaganda + self.gunrunning + self.intelligence + self.sabotage + self.counterint
        super(Spy, self).save(*args, **kwargs)

    def __unicode__(self):
        return unicode('%(owner)s\'s spy currently in %(location)s') % {'owner':self.owner, 'location':self.location}


class NewsItem(models.Model):
    target = models.ForeignKey('World', related_name='newstarget')
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode('to %(a)s: %(b)s...') % {'a':self.target,'b':self.content[0:30]}


class ActionNewsItem(models.Model):
    target = models.ForeignKey('World', related_name='actionnewstarget')
    actiontype = models.IntegerField()
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)

    def _actiontype_display(self):
        if self.actiontype == 1:
            return 'Peace Offer'
        elif self.actiontype == 2:
            return 'Newb Event'
            #expand

    displayactiontype = property(_actiontype_display)

    def __unicode__(self):
        return unicode('%s to %(a)s: %(b)s...') % {'type':self.displayactiontype,'a':self.target,'b':self.content[0:30]}


class Task(models.Model):
    target = models.ForeignKey('World', related_name='tasktarget')
    content = models.TextField()
    taskid = models.CharField(max_length=50, blank=True, null=True, default=None)
    revokable = models.BooleanField(default=False)
    outcome = models.TextField(default='Please wait...')
    datetime = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode('to %(a)s: %(b)s...') % {'a':self.target,'b':self.content[0:30]}


class Comm(models.Model):
    target = models.ForeignKey('World', related_name='commtarget')
    sender = models.ForeignKey('World', related_name='commsender')
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode('from %(a)s to %(b)s: %(c)s...') % {'a':self.sender,'b':self.target,'c':self.content[0:30]}


class SentComm(models.Model):
    sender = models.ForeignKey('World', related_name='sentcommsender')
    target = models.ForeignKey('World', related_name='sentcommtarget')
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)

    def __unicode__(self):
        return unicode('from %(a)s to %(b)s: %(c)s...') % {'a':self.sender,'b':self.target,'c':self.content[0:30]}


class Announcement(models.Model):
    sender = models.ForeignKey('World', related_name='announcementsender')
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)

    def __unicode__(self):
        return unicode('from %(a)s: %(b)s...') % {'a':self.sender,'b':self.content[0:30]}


class War(models.Model):
    attacker = models.ForeignKey('World', related_name='warattacker')
    defender = models.ForeignKey('World', related_name='wardefender')
    region = models.CharField(max_length=1, default='A')
    reason = models.CharField(max_length=20, default="I don't like you.")
    timetonextattack = models.DateTimeField(default=v.now)
    timetonextdefense = models.DateTimeField(default=v.now)
    peaceofferbyatk = models.ForeignKey('ActionNewsItem', related_name='peacebyatk',
                            default=None, blank=True, null=True, on_delete=models.SET_NULL)
    peaceofferbydef = models.ForeignKey('ActionNewsItem', related_name='peacebydef',
                            default=None, blank=True, null=True, on_delete=models.SET_NULL)
    starttime = models.DateTimeField(default=v.now)

    def delete(self, *args, **kwargs):
        ActionNewsItem.objects.filter(target=self.attacker, actiontype=1).delete()
        ActionNewsItem.objects.filter(target=self.defender, actiontype=1).delete()
        super(War, self).delete(*args, **kwargs)

    def __unicode__(self):
        return unicode('%(att)s attacking %(def)s') % {'att':self.attacker,'def':self.defender}


class Trade(models.Model):
    owner = models.ForeignKey('World', related_name='tradeowner')
    resoff = models.IntegerField()
    amountoff = models.IntegerField()
    resrec = models.IntegerField()
    amountrec = models.IntegerField()
    amounttrades = models.IntegerField(default=1)
    datetime = models.DateTimeField(default=v.now)

    def _resourceoff_display(self):
        from wawmembers.utilities import resname
        return resname(self.resoff, self.amountoff, lower=True)
    displayoff = property(_resourceoff_display)

    def _resourcerec_display(self):
        from wawmembers.utilities import resname
        return resname(self.resrec, self.amountrec, lower=True)
    displayrec = property(_resourcerec_display)

    def __unicode__(self):
        return unicode('%(owner)s offering %(amountoff)s %(resoff)s for %(amountrec)s %(resrec)s.') % \
            {'owner':self.owner,'amountoff':self.amountoff,'resoff':self.displayoff,'amountrec':self.amountrec,'resrec':self.displayrec}


class Agreement(models.Model):
    sender = models.ForeignKey('World', related_name='agreesend')
    receiver = models.ForeignKey('World', related_name='agreerec')
    order = models.IntegerField()
    resource = models.IntegerField()
    available = models.BooleanField(default=True)

    def _resource_display(self):
        from wawmembers.display import trade_display
        return trade_display(self.resource)
    displayres = property(_resource_display)

    def __unicode__(self):
        return unicode('%(sender)s sending %(res)s to %(receiver)s.') % {'sender':self.sender,'res':self.resource,'receiver':self.receiver}


class LotteryTicket(models.Model):
    owner = models.ForeignKey('World', related_name='lotteryowner')


class GlobalData(models.Model):
    rumsoddiumwars = models.IntegerField(default=0)
    turnbackground = models.IntegerField(default=1)
    lotterywinnerid = models.IntegerField(default=1)
    lotterywinneramount = models.IntegerField(default=0)
    corlevel = models.IntegerField(default=5000)
    lcrlevel = models.IntegerField(default=30000)
    deslevel = models.IntegerField(default=95000)
    frilevel = models.IntegerField(default=230000)
    hcrlevel = models.IntegerField(default=460000)
    bcrlevel = models.IntegerField(default=820000)
    bshlevel = models.IntegerField(default=1400000)
    drelevel = models.IntegerField(default=2200000)

    def __unicode__(self):
        return unicode('Global Data')


class Ban(models.Model):
    address = models.CharField(max_length=255, help_text="IP address banned", unique=True)
    reason = models.CharField(max_length=255, help_text="Ban reason")

    def __unicode__(self):
        return unicode("Banned %s: %s" % (self.address, self.reason))

    def save(self, *args, **kwargs):
        cache.add('BAN:'+self.address, '1', None)
        super(Ban, self).save(*args, **kwargs)


class GDPSale(models.Model):
    seller = models.ForeignKey('World', verbose_name="Seller", related_name="gdpseller")
    buyer = models.ForeignKey('World', verbose_name="Buyer", related_name="gdpbuyer")
    gdpamount = models.IntegerField(verbose_name="GDP Amount")
    geuamount = models.IntegerField(verbose_name="GEU Amount")
    date_of_offer = models.DateTimeField(default=v.now)

    def __unicode__(self):
        return "%s %s %s %s" % (self.seller, self.buyer, self.gdpamount, self.geuamount)


class GDPSaleThresholdManager(models.Model):
    target = models.ForeignKey('World', related_name="world")
    buythreshold = models.IntegerField(verbose_name="Buy Threshold Limit")
    sellthreshold = models.IntegerField(verbose_name="Sell Threshold Limit")

    def __unicode__(self):
        return "%s %s %s" % (self.target, self.buythreshold, self.sellthreshold)


class SecurityCookie(models.Model):
    LoggedIn = models.ForeignKey('World', related_name="cookie_world_loggedin", verbose_name="Initial Log In")
    LoggedInB64 = models.CharField(max_length=100, verbose_name='Initial Log in B64')
    MatchB64 = models.CharField(max_length=100, verbose_name='Match B64')
    Match = models.ForeignKey('World', related_name="cookie_world_match", verbose_name="Matched World")
    date = models.DateTimeField(default=v.now, verbose_name="Date of Match")

#######
### LOGS
#######

class ResourceLog(models.Model):
    owner = models.ForeignKey('World', related_name='logresowner')
    target = models.ForeignKey('World', related_name='logrestarget')
    res = models.IntegerField()
    amount = models.IntegerField()
    sent = models.BooleanField()
    trade = models.BooleanField()
    datetime = models.DateTimeField(default=v.now)

    def _res_display(self):
        from wawmembers.utilities import resname
        return resname(self.res, self.amount, lower=True)
    displayres = property(_res_display)

    def _direction_display(self):
        return ('<span style="color:red;">sent</span>' if self.sent else '<span style="color:green;">received</span>')
    displaydirection = property(_direction_display)

    def _log_type(self):
        return ('trade' if self.trade else 'aid')
    displaylogtype = property(_log_type)

    def __unicode__(self):
        if self.sent:
            toreturn = unicode('%(owner)s sent %(amount)s %(res)s to %(target)s by %(type)s.')
        else:
            toreturn = unicode('%(owner)s received %(amount)s %(res)s from %(target)s by %(type)s.')
        return toreturn % {'owner':self.owner,'amount':self.amount, 'res':self.res,'target':self.target,'type':self.displaylogtype}


class WarLog(models.Model):
    owner = models.ForeignKey('World', related_name='logwarowner')
    target = models.ForeignKey('World', related_name='logwartarget')
    victory = models.BooleanField()
    gdp = models.IntegerField(default=0, help_text="million GEU")
    growth = models.IntegerField(default=0, help_text="million GEU")
    budget = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    warpfuel = models.IntegerField(default=0)
    duranium = models.IntegerField(default=0)
    tritanium = models.IntegerField(default=0)
    adamantium = models.IntegerField(default=0)
    fig = models.IntegerField(default=0)
    cor = models.IntegerField(default=0)
    lcr = models.IntegerField(default=0)
    des = models.IntegerField(default=0)
    fri = models.IntegerField(default=0)
    hcr = models.IntegerField(default=0)
    bcr = models.IntegerField(default=0)
    bsh = models.IntegerField(default=0)
    dre = models.IntegerField(default=0)
    fre = models.IntegerField(default=0)
    datetime = models.DateTimeField(default=v.now)

    def _spoils_display(self):
        from wawmembers.newsgenerator import losses
        hlosses = losses([self.fig, self.cor, self.lcr, self.des, self.fri, self.hcr, self.bcr, self.bsh, self.dre])
        toreturn = ''
        if self.gdp != 0:
            toreturn += '%s GDP, ' % self.gdp
        if self.growth != 0:
            toreturn += '%s growth, ' % self.growth
        if self.budget != 0:
            toreturn += '%s GEU, ' % self.budget
        if self.warpfuel != 0:
            toreturn += '%s warpfuel, ' % self.warpfuel
        if self.duranium != 0:
            toreturn += '%s duranium, ' % self.duranium
        if self.tritanium != 0:
            toreturn += '%s tritanium, ' % self.tritanium
        if self.adamantium != 0:
            toreturn += '%s adamantium, ' % self.adamantium
        if self.fre != 0:
            toreturn += '%s freighters, ' % self.fre
        if hlosses != ' no ships at all':
            toreturn += hlosses + '  '
        return ('No spoils' if toreturn == '' else toreturn[:-2])
    displayspoils = property(_spoils_display)

    def _type_display(self):
        return ('<span style="color:green;">won</span>' if self.victory else '<span style="color:red;">lost</span>')
    displaytype = property(_type_display)

    def __unicode__(self):
        desc = ('won' if self.victory else 'lost')
        return unicode('%s %s war against %s. Spoils: %s' % (self.owner, desc, self.target, self.displayspoils))


class BankLog(models.Model):
    alliance = models.ForeignKey('Alliance', related_name='logbankalliance')
    world = models.ForeignKey('World', related_name='logbankworld')
    action = models.BooleanField(default=False)
    amount = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    before = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    after = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    datetime = models.DateTimeField(default=v.now)

    def _action_display(self):
        return ('deposited' if self.action else 'withdrew')
    displayaction = property(_action_display)

    def __unicode__(self):
        return unicode('%(world)s %(display)s %(amount)s GEU - Before: %(before)s, After: %(after)s. %(t)s') % \
            {'world':self.world,'display':self.displayaction,'amount':self.amount,'before':self.before,'after':self.after,'t':self.datetime}


class AllianceLog(models.Model):
    alliance = models.ForeignKey('Alliance', related_name='logactionsalliance')
    officer = models.ForeignKey('World', related_name='logactionsofficer', blank=True, null=True)
    world = models.ForeignKey('World', related_name='logactionsworld')
    logtype = models.IntegerField()
    datetime = models.DateTimeField(default=v.now)

    def __unicode__(self):
        if self.logtype == 0:    # make invitation
            toreturn = '%(officer)s invited %(world)s to join'
        elif self.logtype == 1:  # withdraw invitation
            toreturn = '%(officer)s revoked %(world)s\'s invite to join'
        elif self.logtype == 2:  # accept invitation
            toreturn = '%(world)s accepted an invite to join'
        elif self.logtype == 3:  # promotion to officer
            toreturn = '%(officer)s promoted %(world)s to be an officer'
        elif self.logtype == 4:  # demotion from officer
            toreturn = '%(officer)s demoted %(world)s from officership'
        elif self.logtype == 5:  # resign from officer
            toreturn = '%(world)s resigned his officership'
        elif self.logtype == 6:  # purge
            toreturn = '%(officer)s purged %(world)s from the federation'
        elif self.logtype == 7:  # leaving
            toreturn = '%(world)s left the alliance'
        elif self.logtype == 8:  # successor
            toreturn = '%(officer)s gave leadership to %(world)s'
        return unicode(toreturn) % {'officer':self.officer,'world':self.world}


class AgreementLog(models.Model):
    owner = models.ForeignKey('World', related_name='logagreeowner')
    target = models.ForeignKey('World', related_name='logagreetarget')
    resource = models.IntegerField()
    logtype = models.IntegerField()
    seen = models.BooleanField(default=False)
    datetime = models.DateTimeField(default=v.now)

    def _resource_display(self):
        from wawmembers.display import trade_display
        return trade_display(self.resource)
    displayres = property(_resource_display)

    def __unicode__(self):
        from wawmembers.display import trade_display
        if self.logtype == 0: # make agreement
            toreturn = '%(target)s made agreement to send you one %(res)s'
        elif self.logtype == 1: # revoke agreement
            toreturn = '%(target)s revoked agreement to send you one %(res)s'
        elif self.logtype == 2: # broken due to opposite econ
            toreturn = '%(target)s agreement to send you one %(res)s broken down, opposite alignment'
        elif self.logtype == 3: # broken due to opposite econ
            toreturn = '%(target)s refused agreement to be sent one %(res)s'
        elif self.logtype == 4: # no freighter (owner)
            toreturn = '%(target)s did not receive his %(res)s this turn due to lack of freighter'
        elif self.logtype == 5: # no freighter (receiver)
            toreturn = '%(target)s did not receive his %(res)s this turn due to lack of freighter'
        return toreturn % {'target':self.target, 'res':trade_display(self.resource)}
