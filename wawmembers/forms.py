# Django Imports
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
#from registration.forms import RegistrationFormUniqueEmail as regform

# WaW Imports
from wawmembers.models import *
import wawmembers.variables as v
import wawmembers.utilities as utilities

'''
The logic behind every html form. Names should be self-explanatory.
'''
#no fucking logic here heidi
# Re-used lists

REGION_CHOICES = (
    ('amyntas', 'Amyntas'),
    ('bion', 'Bion'),
    ('cleon', 'Cleon'),
    ('draco', 'Draco'),
)

shiplist = [('1','Fighters'),
            ('2','Corvettes'),
            ('3','Light Cruisers'),
            ('4','Destroyers'),
            ('5','Frigates'),
            ('6','Heavy Cruisers'),
            ('7','Battlecruisers'),
            ('8','Battleships'),
            ('9','Dreadnoughts'),
            ]

RESOURCE_CHOICES = (
    ('budget', 'GEU'),
    ('warpfuel', 'Warpfuel'),
    ('duranium', 'Duranium'),
    ('tritanium', 'Tritanium'),
    ('adamantium', 'Adamantium')
    )

# Forms

class NewWorldForm(forms.Form):

    ECON_CHOICES = (
        (1,'Free Market'),
        (0,'Mixed Economy'),
        (-1,'Central Planning'),
    )

    POL_CHOICES = (
        (80,'Liberal Democracy'),
        (40,'Totalitarian Democracy'),
        (0,'Single-party Rule'),
        (-40,'Fleet Admiralty'),
        (-80,'Autocracy'),
    )

    worldname = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class':'countable','maxlength':'20'}), label="World Name")
    region = forms.ChoiceField(choices=REGION_CHOICES, widget=forms.RadioSelect(attrs={'id':'radioregion'}), label="Sector")
    econsystem = forms.IntegerField(widget=forms.RadioSelect(choices=ECON_CHOICES, attrs={'id':'radioecon'}), label="Economic System")
    polsystem = forms.IntegerField(widget=forms.RadioSelect(choices=POL_CHOICES, attrs={'id':'radiopol'}), label="Political System")


class Blueprinttradeform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(Blueprinttradeform, self).__init__(*args, **kwargs)
        offerchoices = []
        blueprints = world.blueprints.all()
        len(blueprints)
        amounts = []
        for tier in v.shipindices[2:]:
            query = blueprints.filter(model=tier)
            if len(query) > 0:
                for blueprint in query:
                    if blueprint.amount not in amounts:
                        amounts.append(blueprint.amount)
                        offerchoices.append((blueprint.pk, blueprint.__str__()))
        self.fields['offer'] = forms.ChoiceField(choices=offerchoices)
        self.fields['offer_amount'] = forms.IntegerField(min_value=1, label="Amount", widget=forms.NumberInput(
                attrs={'size':'10'}))
        self.fields['amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
        self.fields['amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
        self.fields['amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))



class Shiptradeform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(Shiptradeform, self).__init__(*args, **kwargs)
        fleets = fleet.objects.filter(Q(sector=world.sector)|Q(sector='hangar'), world=world, controller=world)
        choices = []
        for tier in v.shipindices:
            for f in fleets:
                if f.__dict__[tier] > 0:
                    choices.append((tier, tier.replace('_', ' ').capitalize()))
                    break
        exclusionlist = []
        for f in fleets:
            if f.power() == 0:
                exclusionlist.append(f.pk)
        for f in exclusionlist:
            fleets = fleets.exclude(pk=f)
        choices = tuple(choices)
        self.fields['offer'] = forms.ChoiceField(choices=choices, label="Ship type")
        self.fields['fleet'] = forms.ModelChoiceField(queryset=fleets, label="From")
        self.fields['offer_amount'] = forms.IntegerField(min_value=1, label="Amount", widget=forms.NumberInput(
                attrs={'size':'10'}))
        self.fields['request'] = forms.ChoiceField(choices=RESOURCE_CHOICES)
        self.fields['request_amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
        self.fields['amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
    #request = forms.ChoiceField(choices=RESOURCE_CHOICES)
    #request_amount = forms.IntegerField(min_value=1)
    #amount = forms.IntegerField(min_value=1)



class Resourcetradeform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(Resourcetradeform, self).__init__(*args, **kwargs)
        offerchoices = []
        for item in RESOURCE_CHOICES:
            if world.__dict__[item[0]] > 0:
                offerchoices.append(item)
        self.fields['offer'] = forms.ChoiceField(choices=offerchoices)
        self.fields['offer_amount'] = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
    request = forms.ChoiceField(choices=RESOURCE_CHOICES)
    request_amount = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))
    amount = forms.IntegerField(min_value=1, widget=forms.NumberInput(
                attrs={'size':'10'}))



class Accepttradeform(forms.Form):
    def __init__(self, trade, *args, **kwargs):
        super(Accepttradeform, self).__init__(*args, **kwargs)
        self.fields['amount'] = forms.IntegerField(min_value=1, max_value=trade.amount, widget=forms.NumberInput(
                attrs={'size':'2'}))

class FlagForm(forms.Form):

    FLAG_CHOICES = (
        ('fl01','SC Protoss'),
        ('fl02','SC Terran'),
        ('fl03','SC Zerg'),
        ('fl04','ST UFP'),
        ('fl05','ST Terran Empire'),
        ('fl21','ST Romulans'),
        ('fl22','ST Borg'),
        ('fl19','ST Klingons'),
        ('fl06','SW Republic'),
        ('fl07','SW Jedi Order'),
        ('fl08','SW Rebel Alliance'),
        ('fl16','WH40k Imperium'),
        ('fl12','WH40k Chaos'),
        ('fl24','WH40K Tau'),
        ('fl27','WH40K Necron'),
        ('fl31','Half-Life'),
        ('fl18','Halo UNSC'),
        ('fl20','Halo Covenant'),
        ('fl15','DE Tai Yong Medical'),
        ('fl13','DE Sarif Industries'),
        ('fl29','Weyland-Yutani'),
        ('fl23','Mass Effect'),
        ('fl32','Justice'),
        ('fl28','Dr Who TARDIS'),
        ('fl17','Stargate'),
        ('fl14','Battlestar Galactica'),
        ('fl26','XCOM Motto'),
        ('fl09','FO BoS'),
        ('fl59','GHEM'),
        ('fl30','FO Enclave'),
        ('fl10','Spore'),
        ('fl11','Futurama'),
        ('fl25','April Fool\'s'),
    )

    flag = forms.CharField(max_length=4, widget=forms.Select(choices=FLAG_CHOICES, attrs={'id':'flagchoice'}))


class AvatarForm(forms.Form):

    AVATAR_CHOICES = (
        ('av01','Jim Raynor'),
        ('av02','Sarah Kerrigan'),
        ('av03','Arcturus Mengsk'),
        ('av09','Zeratul'),
        ('av04','Jean-Luc Picard'),
        ('av05','Jim Kirk'),
        ('av06','Spock'),
        ('av10','Worf'),
        ('av16','Quark'),
        ('av22','Luke Skywalker'),
        ('av08','Yoda'),
        ('av29','Emperor Palpatine'),
        ('av07','Darth Vader'),
        ('av17','Emperor of Man'),
        ('av30','Grey Knight'),
        ('av51','Gabriel Angelos'),
        ('av47','Farseer Idranel'),
        ('av23','Chaos Sorcerer'),
        ('av15','Khornate Beserker'),
        ('av14','Noise Marine'),
        ('av18','Plague Marine'),
        ('av48','Necron Warrior'),
        ('av49','Tyranid Warrior'),
        ('av50','Tau'),
        ('av12','Gordon Freeman'),
        ('av13','Alyx Vance'),
        ('av24','Vortigaunt'),
        ('av56','Metro Cop'),
        ('av11','Adam Jensen'),
        ('av35','Lawrence Barrett'),
        ('av37','Yelena Fedorova'),
        ('av46','Jaron Namir'),
        ('av60','Hugh Darrow'),
        ('av72','Judge Dredd'),
        ('av34','Master Chief'),
        ('av57','Cortana'),
        ('av36','Thel \'Vadamee'),
        ('av42','Predator'),
        ('av43','Alien'),
        ('av58','Ellen Ripley'),
        ('av59','Lance Bishop'),
        ('av31','Cmdr. Shepard'),
        ('av27','FemShep'),
        ('av99','GHEM'),
        ('av61','Garrus Vakarian'),
        ('av62','Legion'),
        ('av65','Mordin Solus'),
        ('av63','Liara T\'soni'),
        ('av64','Tali\'Zorah'),
        ('av28','The Illusive Man'),
        ('av33','Harbinger'),
        ('av41','10th Dr Who'),
        ('av26','Jack O\'Neill'),
        ('av25','Teal\'c'),
        ('av21','Bill Adama'),
        ('av20','Starbuck'),
        ('av19','Number Six'),
        ('av40','XCOM Soldier'),
        ('av39','XCOM Sectoid'),
        ('av52','Enclave Trooper'),
        ('av32','SHODAN'),
        ('av73','Boron'),
        ('av74','Paranid'),
        ('av75','Split'),
        ('av76','Teladi'),
        ('av38','Mr House'),
        ('av44','Terminator'),
        ('av45','Roy Batty'),
        ('av67','Steve'),
        ('av66','Grox'),
        ('av54','Fry'),
        ('av55','Leela'),
        ('av53','Bender'),
        ('av70','E.T.'),
        ('av68','Isaac Clarke'),
        ('av69','Kyubey'),
        ('av71','April Fool\'s'),
    )

    avatar = forms.CharField(max_length=4, widget=forms.Select(choices=AVATAR_CHOICES, attrs={'id':'avatarchoice'}))


class Aidform(forms.Form):

    def __init__(self, world, *args, **kwargs):
        super(Aidform, self).__init__(*args, **kwargs)
        reslist = (
            ('budget', 'GEU'), 
            ('warpfuel', 'Warpfuel'),
            ('duranium', 'Duranium'), 
            ('tritanium', 'Tritanium'), 
            ('adamantium', 'Adamantium')
        )
        choicelist = []
        for field in reslist:
            if world.__dict__[field[0]] > 0: #if resource count > 0
                choicelist.append(field) #this gives is hella dynamic forms

        
        #django loves tuples, so
        for resource in choicelist:
            max_number = world.__dict__[resource[0]]
            self.fields[resource[0]] = forms.IntegerField(widget=forms.NumberInput(
                attrs={'size':'10'}), label="%s: " % resource[1], min_value=0, max_value=max_number)

class Shipaidform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(Shipaidform, self).__init__(*args, **kwargs)
        fleets = fleet.objects.filter((Q(sector=world.sector)|Q(sector='hangar')), world=world, controller=world)
        techlist = (
            ('freighters', 'Freighters'),
            ('fighters', 'Fighters'),
            ('corvettes', 'Corvettes'),
            ('light_cruisers', 'Light Cruisers'),
            ('destroyers', 'Destroyers'),
            ('frigates', 'Frigates'), 
            ('heavy_cruisers', 'Heavy Cruisers'), 
            ('battlecruisers', 'Battlecruisers'), 
            ('battleships', 'Battleships'),
            ('dreadnoughts', 'Dreadnoughts')
        )
        choicelist = []
        comparisonfleet = fleet()
        for ball in fleets:
            comparisonfleet.merge(ball)
        for field in techlist:
            if comparisonfleet.__dict__[field[0]] > 0:
                choicelist.append(field)
        choicelist = tuple(choicelist)
        self.fields["ship_choice"] = forms.ChoiceField(choices=choicelist)
        self.fields["fleet_choice"] = forms.ModelChoiceField(queryset=fleets)
    amount = forms.IntegerField(min_value=1)

class aidfleetform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(aidfleetform, self).__init__(*args, **kwargs)
        query = world.controlled_fleets.all().exclude(sector='warping').exclude(sector='hangar')
        self.fields['fleetchoice'] = forms.ModelChoiceField(queryset=query)
        self.fields['retain_control'] = forms.BooleanField(label="Retain ownership")

class mineshutdownform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(mineshutdownform, self).__init__(*args, **kwargs)
        choices = []
        for prodtype in v.productionindices:
            if world.__dict__[prodtype] >= v.production[prodtype]['production']:
                choices.append((prodtype, prodtype[:-4].capitalize()))
        self.fields['mine'] = forms.ChoiceField(choices=choices)

class reopenmineform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(reopenmineform, self).__init__(*args, **kwargs)
        choices = []
        for prodtype in v.productionindices:
            prod = 'inactive_%s' % prodtype
            if world.__dict__[prod] > 0:
                choices.append((prodtype, prodtype[:-4].capitalize()))
        self.fields['mine'] = forms.ChoiceField(choices=choices)

class GalaxySortForm(forms.Form):

    SORT_CHOICES = (
        ('pk','ID, ascending'),
        ('-pk','ID, descending'),
        ('gdp','GDP, ascending'),
        ('-gdp','GDP, descending'),
        ('name','World name, ascending'),
        ('-name','World name, descending'),
        ('user__username','Username, ascending'),
        ('-user__username','Username, descending'),
        ('warpoints','War points, ascending'),
        ('-warpoints','War points, descending'),
    )

    sortby = forms.CharField(max_length=20, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'sortselect'}), label="Sort By")


class ResearchForm(forms.Form):

    researchamount = forms.IntegerField(label="GEU Amount")


#class RegistrationUniqueEmailCounters(regform):

 #   username = forms.RegexField(regex=r'^[\w.@+-]+$', max_length=30, label=_("Username"),
 #       error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")},
  #      widget=forms.TextInput(attrs={'class': 'countable', 'maxlength': '30',}))


class CommDisplayForm(forms.Form):

    SORT_CHOICES = (
        ('new','New (group by sender, then chrono)'),
        ('old','Old (simple chronological order)'),
    )

    sortby = forms.CharField(max_length=10, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'sortselect'}), label="Comm Display")


class FlagDisplayForm(forms.Form):

    SORT_CHOICES = (
        ('new','Show world flags on the list page'),
        ('old','Omit world flags from the list page'),
    )

    flagpref = forms.CharField(max_length=10, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'flagselect'}), label="Flag Display")


class SelectSpyForm(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(SelectSpyForm, self).__init__(*args, **kwargs)

        spies = list(Spy.objects.filter(owner=world, location=world))

        SPY_CHOICES = [(spy.pk, spy.name) for spy in spies]

        self.fields["spyselect"] = forms.IntegerField(widget=forms.Select(choices=SPY_CHOICES), label="Select Spy")


class DeleteByTargetForm(forms.Form):
    def __init__(self, world, logtype, *args, **kwargs):
        super(DeleteByTargetForm, self).__init__(*args, **kwargs)

        if logtype == 'war':
            listlogs = Warlog.objects.filter(owner=world)

            listtargets = []
            for log in listlogs:
                if log.target not in listtargets:
                    listtargets.append(log.target)

        elif logtype == 'res':
            listlogs = ResourceLog.objects.filter(owner=world)

            listtargets = []
            for log in listlogs:
                if log.target not in listtargets:
                    listtargets.append(log.target)

        elif logtype == 'reccomm':
            listlogs = Comm.objects.filter(target=world)

            listtargets = []
            for log in listlogs:
                if log.sender not in listtargets:
                    listtargets.append(log.sender)

        elif logtype == 'sentcomm':
            listlogs = SentComm.objects.filter(sender=world)

            listtargets = []
            for log in listlogs:
                if log.target not in listtargets:
                    listtargets.append(log.target)

        TARGET_CHOICES = [(target.pk, target.name) for target in listtargets]

        self.fields["target"] = forms.IntegerField(widget=forms.Select(choices=TARGET_CHOICES), label="Select World")


class BackgroundForm(forms.Form):

    backgrounds = [-2,-1] + range(1,11)

    BG_CHOICES = [(-1, 'Page Rotation'), (-2, 'Turn Rotation')] + [(i,i) for i in sorted(backgrounds) if str(i)[0] != '-']

    background = forms.IntegerField(widget=forms.Select(choices=BG_CHOICES, attrs={'id':'bgchoice'}), label="Background")


class PolicyChoiceForm(forms.Form):

    SORT_CHOICES = (
        ('js','Tooltip with choices'),
        ('econ','Economic policies'),
        ('domestic','Domestic policies'),
        ('diplomacy','Diplomatic policies'),
        ('military','Fleet policies'),
    )

    policychoice = forms.CharField(max_length=10, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'policyselect'}), label="Policy Link")


class ShipChoiceForm(forms.Form):

    SORT_CHOICES = (
        ('ind','Build a number of an individual ship'),
        ('multi','Set numbers to build a variety of ships'),
    )

    buildchoice = forms.CharField(max_length=5, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'buildselect'}), label="Ship Build Type")


class PersonalShipForm(forms.Form):
    def __init__(self, fleets, *args, **kwargs):
        super(PersonalShipForm, self).__init__(*args, **kwargs)
        self.fields['fleetchoice'] = forms.ModelChoiceField(queryset=fleets)
    SHIP_CHOICES = (
        ('1','Personal Fighter'),
        ('2','Militarised Yacht'),
        ('3','Command Ship'),
    )

    shiptype = forms.IntegerField(widget=forms.Select(choices=SHIP_CHOICES, attrs={'id':'flagshipselect'}), label="Ship Type")


class PersonalShipPicForm(forms.Form):

    def __init__(self, shiptype, *args, **kwargs):
        super(PersonalShipPicForm, self).__init__(*args, **kwargs)

        if shiptype == 1:
            PSPIC_CHOICES = [('pf01','1'),
                             ('pf02','2'),
                             ('pf03','3'),
                             ('pf04','4'),
                             ('pf05','5'),
                             ('pf06','6'),
                             ('pf07','7'),
                             ('pf08','8'),
                             ('pf09','9'),
                             ('pf10','10')]

        elif shiptype == 2:
            PSPIC_CHOICES = [('my01','1'),
                             ('my02','2'),
                             ('my03','3'),
                             ('my04','4'),
                             ('my05','5'),
                             ('my06','6'),
                             ('my07','7'),
                             ('my08','8'),
                             ('my09','9'),
                             ('my10','10')]

        else:
            PSPIC_CHOICES = [('cs01','1'),
                             ('cs02','2'),
                             ('cs03','3'),
                             ('cs04','4'),
                             ('cs05','5'),
                             ('cs06','6'),
                             ('cs07','7'),
                             ('cs08','8'),
                             ('cs09','9'),
                             ('cs10','10')]

        self.fields["pspic"] = forms.CharField(max_length=4, widget=forms.Select(choices=PSPIC_CHOICES, attrs={'id':'pspicchoice'}),
            label="Ship Picture")


class Shipexchangeform(forms.Form):
    def __init__(self, fleet1, fleet2, *args, **kwargs):
        super(Shipexchangeform, self).__init__(*args, **kwargs)
        self.highest = None
        self.fleet1 = fleet1.pk
        self.fleet2 = fleet2.pk
        for ship in v.shipindices:
            if fleet1.__dict__[ship] > 0 or fleet2.__dict__[ship] > 0:
                self.highest = ship
        for ship in v.shipindices[:v.shipindices.index(self.highest)+1]: #only ships in fleet
            maxships = fleet1.__dict__[ship] + fleet2.__dict__[ship]
            self.fields['%s %s' % (fleet1.pk, ship)] = forms.IntegerField(min_value=0, 
                max_value=maxships, widget=forms.NumberInput(attrs={'size':'4'}))
            self.fields['%s %s' % (fleet2.pk, ship)] = forms.IntegerField(min_value=0, 
                max_value=maxships, widget=forms.NumberInput(attrs={'size':'4'}))

    def clean(self):
        super(Shipexchangeform, self).clean()
        data = self.cleaned_data
        flag = True
        for ship in v.shipindices[:v.shipindices.index(self.highest)+1]:
            key1 = '%s %s' % (self.fleet1, ship)
            key2 = '%s %s' % (self.fleet2, ship)
            print key1, key2
            total = data[key1] + data[key2]
            if total > self['%s %s' % (self.fleet1, ship)].field.max_value:
                self.add_error('%s %s' % (self.fleet1, ship), "Too many %s" % ship.replace('_', ' '))
            elif total < self['%s %s' % (self.fleet1, ship)].field.max_value:  
                self.add_error('%s %s' % (self.fleet1, ship), "Too few %s" % ship.replace('_', ' '))


#dynamic ship building form
class shipbuildform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(shipbuildform, self).__init__(*args, **kwargs)
        techlist = ['Freighter']
        shiplist = techlist + v.tiers[:v.tiers.index(world.techlevel)+1]
        #slicing up the tech list allows for a dynamic amount of fields
        for ship in shiplist:
            self.fields['%s' % ship.replace(' ', '_').lower() + 's'] = forms.IntegerField(min_value=1, initial=0, required=False)
            #easier than a long if else if chain
    

class trainfleetform(forms.Form):
    def __init__(self, pk, *args, **kwargs):
        super(trainfleetform, self).__init__(*args, **kwargs)
        query = fleet.objects.filter(world=pk).exclude(sector='hangar')
        query = query.exclude(sector='warping')
        self.fields['fleet'] = forms.ModelChoiceField(queryset=query, 
            label="Fleet to train", widget=forms.Select(attrs={'id': 'trainchoice', 'onchange': 'trainfleetcost()'}))


class fleetwarpform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(fleetwarpform, self).__init__(*args, **kwargs)
        query = fleet.objects.filter(controller=world).exclude(sector="hangar").exclude(sector="warping")
        choices = []
        for sfleet in query:
            choices.append((sfleet.pk, sfleet.name + " - " + sfleet.sector))
        choices = tuple(choices)
        self.fields['fleet'] = forms.ChoiceField(choices=choices, label="Select fleet to warp")
    destination = forms.ChoiceField(choices=REGION_CHOICES)

class attackform(forms.Form):
    def __init__(self, world, sector, *args, **kwargs):
        super(attackform, self).__init__(*args, **kwargs)
        query = world.controlled_fleets.all().exclude(sector='hangar').exclude(sector='warping')
        query = query.filter(sector=sector)
        exclude_list = []
        for f in query:
            if f.power() == 0 or f.powermodifiers() == 0:
                exclude_list.append(f.pk)
        for pk in exclude_list:
            query = query.exclude(pk=pk)

        self.fields['fleets'] = forms.ModelMultipleChoiceField(queryset=query, widget=forms.SelectMultiple(
            attrs={'style': 'color: black; background-color: white; min-width: 80px;'}))


class buildlocationform(forms.Form):
    def __init__(self, world, *args, **kwargs):
        super(buildlocationform, self).__init__(*args, **kwargs)
        query = fleet.objects.filter(
            Q(sector=world.sector)|Q(sector='hangar'),
            controller=world)
        self.fields['buildchoice'] = forms.ModelChoiceField(queryset=query)
        self.fields['recievechoice'] = forms.ModelChoiceField(queryset=query)

class noinput(forms.Form):
    number = forms.IntegerField(min_value=0)

class fleetnamechangeform(forms.Form):
    name = forms.CharField(max_length=25)

class sectorchoice(forms.Form):
    choice = forms.ChoiceField(choices=REGION_CHOICES)

class mergeform(forms.Form):
    def __init__(self, world, fleetobj, *args, **kwargs):
        super(mergeform, self).__init__(*args, **kwargs)
        if fleetobj.sector == 'hangar':
            fleets = world.fleets.all().filter(sector=world.sector, controller=world)
        elif fleetobj.sector == world.sector:
            fleets = world.fleets.all().filter(Q(sector=world.sector)|Q(sector='hangar'), 
                controller=world).exclude(pk=fleetobj.pk)
        elif fleetobj.sector == 'warping':
            fleets = world.fleets.all().exclude(pk__gte=0) #invalid so niggas who try get no results
        else:
            fleets = world.fleets.all().filter(sector=fleetobj.sector, controller=world).exclude(pk=fleetobj.pk)

        self.fields['fleetchoice'] = forms.ModelChoiceField(queryset=fleets, widget=forms.Select(attrs={'style':'max-width: 105px'}))


class lootpriorityform(forms.Form):
    gdp = forms.IntegerField(min_value=0)
    growth = forms.IntegerField(min_value=0)
    warpfuel = forms.IntegerField(min_value=0)
    duranium = forms.IntegerField(min_value=0)
    tritanium = forms.IntegerField(min_value=0)
    adamantium = forms.IntegerField(min_value=0)

class passchange(forms.Form):
    oldpass = forms.CharField(widget=forms.PasswordInput, max_length=40, label="Old password")
    new1 = forms.CharField(widget=forms.PasswordInput, max_length=40, label="New password")
    new2 = forms.CharField(widget=forms.PasswordInput, max_length=40, label="New password again")

class donorurlform(forms.Form):
    url = forms.CharField(max_length=30, required=False)

class tradeamountform(forms.Form):
    def __init__(self, trade, *args, **kwargs):
        super(tradeamountform, self).__init__(*args, **kwargs)
        if trade.offer_type == 'resource':
            val = trade.owner.__dict__[trade.offer] / trade.offer_amount
        elif trade.offer_type == 'ship':
            val = trade.fleet_source.__dict__[trade.offer]
        elif trade.offer_type == 'blueprint':
            bp = Blueprint_license.objects.get(pk=trade.blueprint_pk)
            val = trade.owner.blueprints.all().filter(model=bp.model, amount=bp.amount)
        maxval = val / trade.offer_amount
        self.fields['tradeno'] = forms.IntegerField(min_value=1, max_value=maxval)

