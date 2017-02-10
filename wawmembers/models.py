# Django Imports
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

# Python Imports
import decimal

# WaW Imports
import wawmembers.variables as v

'''
All objects live here. This is the interface between Python and database data.
'''

# most of these should be positive integer fields


D = decimal.Decimal


class World(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    world_descriptor = models.CharField(max_length=100, default='The World of', verbose_name="world title")
    leadertitle = models.CharField(max_length=100, default='Leader', verbose_name="leader title")
    name = models.CharField(max_length=20)
    world_desc = models.TextField(max_length=500, blank=True,
        default='Welcome to Worlds at War! [br] Go to the settings page to change this description!')

    creationtime = models.DateTimeField(default=v.now, verbose_name="creation time")
    lastloggedintime = models.DateTimeField(default=v.now, verbose_name="last logged in time")

    creationip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="creation IP")
    lastloggedinip = models.GenericIPAddressField(default='127.0.0.1', verbose_name="last logged in IP")
    sector = models.CharField(max_length=7, default='amyntas')

    tempmsg = models.CharField(max_length=200, null=True, default=None)

    galaxysort = models.CharField(max_length=200, default='pk')
    commpref = models.CharField(max_length=10, default='new')
    flagpref = models.CharField(max_length=10, default='new')
    worlddisplayno = models.IntegerField(default=20)
    statsopenprefs = models.CharField(max_length=50, default='domestic,economic,diplomacy,military')
    backgroundpref = models.IntegerField(default=-1)
    policypref = models.CharField(max_length=10, default='js')

    # Economy
    econsystem = models.IntegerField(verbose_name="economics System", default=0,
        help_text="-1: Central Planning. 0: Mixed Economy. 1: Free Market.")

    gdp = models.PositiveIntegerField(default=500, help_text="million GEU")
    budget = models.DecimalField(default=1000, max_digits=18, decimal_places=1, help_text="GEU")
    growth = models.IntegerField(default=2, help_text="million GEU")

    missed_upkeep = models.DecimalField(default=0, max_digits=6, decimal_places=1)

    econchanged = models.BooleanField(default=False)

    def _res_display(self):
        from wawmembers.utilities import trade_display
        return trade_display(self.resource)
    displayresource = property(_res_display)

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
    warpfuel = models.PositiveIntegerField(default=25)
    warpfuelprod = models.PositiveIntegerField(default=10)
    inactive_warpfuelprod = models.IntegerField(default=0)
    resuming_warpfuelprod = models.IntegerField(default=0)
    duranium = models.PositiveIntegerField(default=12)
    duraniumprod = models.PositiveIntegerField(default=3)
    inactive_duraniumprod = models.IntegerField(default=0)
    resuming_duraniumprod = models.IntegerField(default=0)
    tritanium = models.PositiveIntegerField(default=0)
    tritaniumprod = models.PositiveIntegerField(default=0)
    inactive_tritaniumprod = models.IntegerField(default=0)
    resuming_tritaniumprod = models.IntegerField(default=0)
    adamantium = models.PositiveIntegerField(default=0)
    adamantiumprod = models.PositiveIntegerField(default=0)
    inactive_adamantiumprod = models.IntegerField(default=0)
    resuming_adamantiumprod = models.IntegerField(default=0)

    freighters = models.PositiveIntegerField(default=2)
    freightersinuse = models.PositiveIntegerField(default=0)

    salvdur = models.PositiveIntegerField(default=0, verbose_name="salvage duranium")
    salvtrit = models.PositiveIntegerField(default=0, verbose_name="salvage tritanium")
    salvadam = models.PositiveIntegerField(default=0, verbose_name="salvage adamantium")
    turnsalvaged = models.BooleanField(default=False)

    # General Military
    millevel = models.PositiveIntegerField(default=0, verbose_name="military Level")
    #^money sunk into research
    techlevel = models.CharField(max_length=20, default="Fighter")
    #level for easier comparison
    turnresearched = models.BooleanField(default=False)
    warpoints = models.PositiveIntegerField(default=0)

    timetonextadmiralty = models.DateTimeField(default=v.now, verbose_name="next admiralty")

    warsperturn = models.PositiveIntegerField(default=0)
    declaredwars = models.ManyToManyField('World', related_name='declaredwars+', default=None, blank=True)
    noobprotect = models.BooleanField(default=True)

    warprotection = models.DateTimeField(default=v.nowplusweek, verbose_name="war protection")
    abovegdpprotection = models.DateTimeField(default=v.now, verbose_name="higher-gdp protection")
    brokenwarprotect = models.DateTimeField(default=v.now, verbose_name="time till able to get protection")

    shipyards = models.PositiveIntegerField(default=2)
    productionpoints = models.PositiveIntegerField(default=24)

    shipsortprefs = models.CharField(max_length=50, default='prodhome,sendhome,receivehome')

    flagshiptype = models.PositiveIntegerField(default=0,
        help_text="""
        0: No Flagship, 1: Personal Fighter, 2: Militarised Yacht, 3: Command Ship
        """)
    flagshipbuild = models.BooleanField(default=False)
    flagshipname = models.CharField(max_length=30, default='Executor')
    flagshippicture = models.CharField(max_length=4,default='pf01')
    donatorflagship = models.CharField(max_length=200, default='http://wawgame.eu/static/personalships/my10.gif')

    #Alliance
    alliance = models.ForeignKey('Alliance', related_name='allmember',
        default=None, blank=True, null=True, on_delete=models.SET_NULL)
    alliancepaid = models.BooleanField(default=False)
    officer = models.NullBooleanField(default=False)
    leader = models.NullBooleanField(default=False)

    # Meta
    reset = models.BooleanField(default=False) #for better resets and keeping world IDs
    def __unicode__(self): 
        return unicode(self.name)

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        if self.preferences.donor:
            if len(self.preferences.donorurl.url) > 0:
                return reverse('stats_ind', kwargs={'url': self.preferences.donorurl.url})
        return reverse('stats_ind', kwargs={'url': (str(self.pk))})

    def buildcapacity(self):
        info = { #makes it easier to compare build costs
        'geu': self.budget,
        'duranium': self.duranium,
        'tritanium': self.tritanium,
        'adamantium': self.adamantium,
        'productionpoints': self.productionpoints
        }
        return info

    def _region_display(self):
        return self.sector.capitalize()
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
        return ('<span style=\"color:steelblue;\">%s</span>' % self.user.username if self.preferences.donor else self.user.username)
    displayname = property(_name_display)

    def delete(self, *args, **kwargs):
        #nullworld = World.objects.get(pk=0)
        # move spies back
        for spy in Spy.objects.filter(location=self):
            data = 'The world your spy was in has been deleted, so your spy has been returned.'
            NewsItem.objects.create(target=spy.owner, content=data)
            spy.locationreset()
        super(World, self).delete(*args, **kwargs)

#ditching the fuck out of the retarded ship implementation
#in favor of a bloc5-like implementation
class fleet(models.Model):
    world = models.ForeignKey(World, related_name="fleets")
    controller = models.ForeignKey(World, related_name="controlled_fleets")
    sector = models.CharField(max_length=7, default="amyntas") #amyn, bi, cle, draco and warping
    name = models.CharField(max_length=20)
    attacked = models.BooleanField(default=False)
    flagship = models.BooleanField(default=False)
    weariness = models.PositiveIntegerField(default=200)
    training = models.PositiveIntegerField(default=0)
    freighters = models.IntegerField(default=0)
    fighters = models.IntegerField(default=0)
    corvettes = models.IntegerField(default=0)
    light_cruisers = models.IntegerField(default=0)
    destroyers = models.IntegerField(default=0)
    frigates = models.IntegerField(default=0)
    heavy_cruisers = models.IntegerField(default=0)
    battlecruisers = models.IntegerField(default=0)
    battleships = models.IntegerField(default=0)
    dreadnoughts = models.IntegerField(default=0)
    def __unicode__(self):
        return u"%s" % self.name

    def __eq__(self, comp):
        if type(comp) != type(self):
            return False
        for field in list(self._meta.fields)[v.fleetindex+1:]: #we don't compare with freighters
            if self.__dict__[field.name] != comp.__dict__[field.name]:
                return False
        return True
    #merges build queue into fleet
    def mergeorder(self, newships):
        #this is arguably simpler than manually typing out variable names
        #and assigning the new ships to them
        #this is also more portable
        #doesn't need to be edited if more ship types are added
        for field in list(self._meta.fields)[v.fleetindex:]:
            self.__dict__[field.name] += newships.__dict__[field.name]
        newships.delete()

    #merges one fleet with another
    def merge(self, newships):
        for field in list(newships._meta.fields)[v.fleetindex:]:
            self.__dict__[field.name] += newships.__dict__[field.name]
        self.training += newships.training

    def move(self, sector):
        self.sector = sector

    def fuelcost(self):
        fuel = 0
        fuellist = v.shipcosts()
        for field in list(self._meta.fields)[v.fleetindex:]:
            fuel += self.__dict__[field.name] * fuellist[field.name]['fuel']
        if self.flagship:
            fuel += 5
        return fuel

    def trainingcost(self):
        cost = (self.maxtraining() * self.ratio() / 1.5) + 10
        return D(cost).quantize(D('.1'))

    #called when you train
    def train(self, combat=False):
        maxt = self.maxtraining()
        training = maxt / 10
        if combat:
            training *= 0.7
            training = round(training)
        self.training += training
        if self.training > maxt:
            self.training = maxt

    def maxtraining(self):
        maxt = 0
        for field in v.training_costs:
            maxt += self.__dict__[field] * v.training_costs[field]
        return maxt * 10

    def basepower(self):
        power = 0
        powerlist = v.shipcosts()
        for field in list(self._meta.fields)[v.fleetindex:]:
            power += self.__dict__[field.name] * powerlist[field.name]['firepower']
        if self.flagship:
            power += 50
        return power

    def powermodifiers(self):
        try:
            ratio = float(self.training)/float(self.maxtraining())
        except:
            ratio = 0
        trainingmodifer = (ratio/10.0)*5 + 0.5
        wearinessmodifier = (self.weariness/2000.0)*5 + 0.5
        return self.powerfuel() * trainingmodifer * wearinessmodifier

    def bonuspower(self):
        bonus = 0
        shiplist = list(self._meta.fields)[v.fleetindex+1:]#+1 to exclude freighters
        for field in shiplist:
            e = 2
            for ship in shiplist[(shiplist.index(field) + 1):]:
                if self.__dict__[field.name] <= self.__dict__[ship.name] * e:
                    bonus += self.__dict__[field.name]
                else:
                    bonus += self.__dict__[ship.name] * e
                e *= 2
        return bonus

    #returns powah
    def power(self):
        return self.basepower() + self.bonuspower()

    def enoughfuel(self):
        capacity = self.freighters * v.freighter_capacity['total']
        if capacity > self.fuelcost() * v.freighter_capacity['warpfuel'] and \
        self.controller.warpfuel > self.fuelcost():
            return [True, True]
        else:
            if self.freighters * 200 > self.fuelcost():
                return [False, 'warpfuel']
            else:
                return [False, 'freighters']

    #power with fuel taken into account
    #why?
    #because heidi did it
    def powerfuel(self):
        capacity = self.freighters * v.freighter_capacity['total']
        if capacity < self.fuelcost() * v.freighter_capacity['warpfuel']: #not enough freighters
            current = float(capacity / v.freighter_capacity['warpfuel']) / float(self.fuelcost())
        elif self.fuelcost() > self.controller.warpfuel: #not enough avaliable warpfuel
            current = float(self.controller.warpfuel) / float(self.fuelcost())
        else:
            return self.power()
        return self.power() * current #current is how big a percentage of fleet we can supply

    #returns ratio between training level and max training
    def ratio(self):
        try:
            ratio = float(self.training) / float(self.maxtraining())
        except:
            ratio = 0
        return ratio

    #takes a fleet of ships lost and sets ships and training
    def loss(self, lostships):
        ratio = self.ratio()
        for field in list(lostships._meta.fields)[v.fleetindex:]:
            self.__dict__[field.name] -= lostships.__dict__[field.name]
        self.training = int(float(self.maxtraining()) * ratio)

    #heidi legacy
    def heidilist(self):
        l = []
        for field in list(self._meta.fields)[v.fleetindex+1:]:
            l.append(self.__dict__[field.name])
        return l

    def empty(self):
        if sum(self.heidilist()) > 0:
            return False
        return True

    def clear(self):
        a = (True if self.trades.count() == 0 else False)
#production queues
#when a nigga spends his production points on whatever, shit gets added to the queue
#queue consists of these objects
class shipqueue(models.Model):
    fleet = models.ForeignKey(fleet, related_name="orders") #merges with this fleet at turn change
    world = models.ForeignKey(World, related_name="shiporders")
    task = models.OneToOneField('Task', on_delete=models.SET_NULL, blank=True, null=True)
    freighters = models.PositiveIntegerField(default=0)
    fighters = models.PositiveIntegerField(default=0)
    corvettes = models.PositiveIntegerField(default=0)
    light_cruisers = models.PositiveIntegerField(default=0)
    destroyers = models.PositiveIntegerField(default=0)
    frigates = models.PositiveIntegerField(default=0)
    heavy_cruisers = models.PositiveIntegerField(default=0)
    battlecruisers = models.PositiveIntegerField(default=0)
    battleships = models.PositiveIntegerField(default=0)
    dreadnoughts = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return u"%s shipqueue" % self.world.name

    def build(self, formdata):
        for field in formdata:
            self.__dict__[field] = formdata[field]

    def content(self): #returns the contents of the order as a string
        ships = []
        from utilities import resource_text
        for field in v.shipindices:
            if self.__dict__[field] > 0:
                ship = (field if self.__dict__[field] > 1 else field[:-1])
                ships.append([ship.replace('_', ' '), self.__dict__[field]])
        return resource_text(ships)



class preferences(models.Model):
    world = models.OneToOneField(World, on_delete=models.CASCADE)
    donor = models.BooleanField(default=False)
    vacation = models.BooleanField(default=False)
    avatar = models.CharField(max_length=4,default='av01')
    flag = models.CharField(max_length=4,default='fl02')
    donatoravatar = models.CharField(max_length=200, default='none')
    donatorflag = models.CharField(max_length=200, default='none')
    donatoranthem = models.CharField(max_length=200, default='jIxas0a-KgM')
    card = models.CharField(max_length=100, default='None')
    winresource = models.CharField(max_length=11, default='GDP')
    recievefleet = models.OneToOneField(fleet, blank=True, null=True, on_delete=models.SET_NULL, related_name="recieve_fleet")
    buildfleet = models.OneToOneField(fleet, blank=True, null=True, on_delete=models.SET_NULL, related_name="build_fleet")
    #all this shit was moved because we don't need the information every time we need the world
    def __unicode__(self):
        return u"%s prefs" % self.world.name

#small custom URL model for faster loading
class donorurl(models.Model):
    owner = models.OneToOneField(preferences)
    url = models.CharField(max_length=30)

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
    name = models.CharField(max_length=15, default='Name')
    owner = models.ForeignKey('World', related_name='spyowner')
    location = models.ForeignKey('World', related_name='spylocation')
    infiltration = models.PositiveIntegerField(default=0)
    propaganda = models.PositiveIntegerField(default=0)
    gunrunning = models.PositiveIntegerField(default=0)
    intelligence = models.PositiveIntegerField(default=0)
    inteltime = models.DateTimeField(default=v.now)
    resinteltime = models.DateTimeField(default=v.now)
    sabotage = models.PositiveIntegerField(default=0)
    counterint = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    timespent = models.PositiveIntegerField(default=0)
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
    actiontype = models.PositiveIntegerField()
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

#floating salvage from OOS combat
#events assign to planets
class Salvage(models.Model):
    sector = models.CharField(max_length=7, default="amyntas")
    duranium = models.IntegerField(default=0)
    tritanium = models.IntegerField(default=0)
    adamantium = models.IntegerField(default=0)
    def __unicode__(self):
        return u'salvage in %s' % self.sector

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
    sender = models.ForeignKey('World', related_name='commsender', blank=True, null=True, on_delete=models.SET_NULL)
    content = models.TextField()
    datetime = models.DateTimeField(default=v.now)
    seen = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode('from %(a)s to %(b)s: %(c)s...') % {'a':self.sender,'b':self.target,'c':self.content[0:30]}


class SentComm(models.Model):
    sender = models.ForeignKey('World', related_name='sentcommsender')
    target = models.ForeignKey('World', related_name='sentcommtarget', blank=True, null=True, on_delete=models.SET_NULL)
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
    reason = models.CharField(max_length=20, default="I don't like you.")
    lastattack = models.DateTimeField(default=v.now)
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


#so draco can sell their research
class Blueprint_license(models.Model):
    issuer = models.ForeignKey(World, related_name="issued_blueprints")
    owner = models.ForeignKey(World, related_name="blueprints")
    amount = models.IntegerField(default=0)
    model = models.CharField(max_length=15, default="corvettes")

    def __unicode__(self):
        shipmodel = model.replace('_', ' ').capitalize()[:-1]
        return u"%s blueprint, %s runs left" % (model.replace('_', ' '))

class LotteryTicket(models.Model):
    owner = models.ForeignKey('World', related_name='lotteryowner')

class Trade(models.Model):
    owner = models.ForeignKey('World', related_name='trades')
    offer_type = models.CharField(max_length=10, default="resource")
    #resource, blueprint, ship
    offer = models.CharField(max_length=20, default="")
    offer_amount = models.IntegerField(default=1)
    blueprint_type = models.CharField(max_length=20, default="corvettes")
    blueprint_pk = models.IntegerField(default=0) #0 means no actual ID
    fleet_source = models.ForeignKey(fleet, related_name="trades", blank=True, null=True, on_delete=models.CASCADE)
    request = models.CharField(max_length=20, default="")
    request_amount = models.PositiveIntegerField()
    amount = models.PositiveIntegerField(default=1)
    posted = models.DateTimeField(default=v.now) 

    def _resourceoff_display(self):
        if self.offer in v.resources:
            if self.offer == 'budget':
                return 'GEU'
            return self.offer
        from wawmembers.display import training_display
        ship = (self.offer if self.offer_amount > 1 else self.offer[:-1])
        if self.offer == 'freighters':
            return ship
        training_level = training_display(self.fleet_source.training, self.fleet_source.maxtraining())
        return ship + " at " + training_level
    displayoff = property(_resourceoff_display)

    def _resourcerec_display(self):
        if self.request in v.resources:
            if self.request == 'budget':
                return 'GEU'
            return self.request
        return (self.request if self.request_amount > 1 else self.request[:-1])
    displayrec = property(_resourcerec_display)

    def __unicode__(self):
        return u"%ss %s trade" % (self.owner.name, self.offer_type)

class GlobalData(models.Model):
    rumsoddiumwars = models.PositiveIntegerField(default=0)
    turnbackground = models.PositiveIntegerField(default=1)
    corlevel = models.PositiveIntegerField(default=5000)
    lcrlevel = models.PositiveIntegerField(default=30000)
    deslevel = models.PositiveIntegerField(default=95000)
    frilevel = models.PositiveIntegerField(default=230000)
    hcrlevel = models.PositiveIntegerField(default=460000)
    bcrlevel = models.PositiveIntegerField(default=820000)
    bshlevel = models.PositiveIntegerField(default=1400000)
    drelevel = models.PositiveIntegerField(default=2200000)

    def __unicode__(self):
        return unicode('Global Data')

    def tiers(self):
        data = {
        'Corvette': self.corlevel,
        'Light cruiser': self.lcrlevel,
        'Destroyer': self.deslevel,
        'Frigate': self.frilevel,
        'Heavy cruiser': self.hcrlevel,
        'Battlecruiser': self.bcrlevel,
        'Battleship': self.bshlevel,
        'Dreadnought': self.drelevel
        }
        return data


class Ban(models.Model):
    address = models.CharField(max_length=255, help_text="IP address banned", unique=True)
    reason = models.CharField(max_length=255, help_text="Ban reason")

    def __unicode__(self):
        return unicode("Banned %s: %s" % (self.address, self.reason))

    def save(self, *args, **kwargs):
        cache.add('BAN:'+self.address, '1', None)
        super(Ban, self).save(*args, **kwargs)


class SecurityCookie(models.Model):
    LoggedIn = models.ForeignKey('World', related_name="cookie_world_loggedin", verbose_name="Initial Log In")
    LoggedInB64 = models.CharField(max_length=100, verbose_name='Initial Log in B64')
    MatchB64 = models.CharField(max_length=100, verbose_name='Match B64')
    Match = models.ForeignKey('World', related_name="cookie_world_match", verbose_name="Matched World")
    date = models.DateTimeField(default=v.now, verbose_name="Date of Match")

#######
### LOGS
#######
class Fleetloss(models.Model):
    owner = models.ForeignKey(fleet, related_name="loss_logs", on_delete=models.CASCADE)
    against = models.ForeignKey(World, related_name="battle_logs", null=True, blank=True, on_delete=models.SET_NULL)
    time = models.DateTimeField(default=v.now)    

class Shiploss(models.Model):
    log = models.ForeignKey(Fleetloss, related_name="lost_ships", on_delete=models.CASCADE)
    ship = models.CharField(max_length=25, default="no ship")
    amount = models.IntegerField(default=0)

class ResourceLog(models.Model):
    owner = models.ForeignKey('World', related_name='logresowner')
    target = models.ForeignKey('World', related_name='logrestarget', blank=True, null=True, on_delete=models.SET_NULL)
    sent = models.BooleanField(default=False)
    trade = models.BooleanField(default=False)
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
            toreturn = unicode('%s sent.')
        else:
            toreturn = unicode('%s .')
        return toreturn % {'owner':self.owner}

class Logresource(models.Model):
    resource = models.CharField(max_length=25)
    amount = models.IntegerField()
    log = models.ForeignKey(ResourceLog, on_delete=models.CASCADE, related_name="resources")

class Warlog(models.Model):
    owner = models.ForeignKey('World', related_name='logwarowner')
    target = models.ForeignKey('World', related_name='logwartarget', blank=True, null=True, on_delete=models.SET_NULL)
    victory = models.BooleanField()
    gdp = models.PositiveIntegerField(default=0, help_text="million GEU")
    growth = models.PositiveIntegerField(default=0, help_text="million GEU")
    budget = models.DecimalField(default=0, max_digits=18, decimal_places=1, help_text="GEU")
    warpfuel = models.PositiveIntegerField(default=0)
    duranium = models.PositiveIntegerField(default=0)
    tritanium = models.PositiveIntegerField(default=0)
    adamantium = models.PositiveIntegerField(default=0)
    fig = models.PositiveIntegerField(default=0)
    cor = models.PositiveIntegerField(default=0)
    lcr = models.PositiveIntegerField(default=0)
    des = models.PositiveIntegerField(default=0)
    fri = models.PositiveIntegerField(default=0)
    hcr = models.PositiveIntegerField(default=0)
    bcr = models.PositiveIntegerField(default=0)
    bsh = models.PositiveIntegerField(default=0)
    dre = models.PositiveIntegerField(default=0)
    fre = models.PositiveIntegerField(default=0)
    datetime = models.DateTimeField(default=v.now)

    def _spoils_display(self):
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
        return ('No spoils' if toreturn == '' else toreturn[:-2])
    displayspoils = property(_spoils_display)

    def set(self, resources, keys, reverse=False):
        for key in keys:
            if reverse:
                self.__dict__[key] = -resources[key]['amount']
            else:
                self.__dict__[key] = resources[key]['amount']

    def _type_display(self):
        return ('<span style="color:green;">won</span>' if self.victory else '<span style="color:red;">lost</span>')
    displaytype = property(_type_display)

    def __unicode__(self):
        desc = ('won' if self.victory else 'lost')
        return unicode('%s %s war against %s. Spoils: %s' % (self.owner, desc, self.target, self.displayspoils))


class BankLog(models.Model):
    alliance = models.ForeignKey('Alliance', related_name='logbankalliance')
    world = models.ForeignKey('World', related_name='logbankworld', blank=True, null=True, on_delete=models.SET_NULL)
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
    officer = models.ForeignKey('World', related_name='logactionsofficer', blank=True, null=True, on_delete=models.SET_NULL)
    world = models.ForeignKey('World', related_name='logactionsworld', blank=True, null=True, on_delete=models.SET_NULL)
    logtype = models.PositiveIntegerField()
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