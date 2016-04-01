# Django Imports
from django import forms
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationFormUniqueEmail as regform

# WaW Imports
from wawmembers.models import *
import wawmembers.variables as v
import wawmembers.utilities as utilities

'''
The logic behind every html form. Names should be self-explanatory.
'''

# Re-used lists

REGION_CHOICES = (
    ('A', 'Amyntas'),
    ('B', 'Bion'),
    ('C', 'Cleon'),
    ('D', 'Draco'),
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
    region = forms.CharField(max_length=1, widget=forms.RadioSelect(choices=REGION_CHOICES, attrs={'id':'radioregion'}), label="Sector")
    econsystem = forms.IntegerField(widget=forms.RadioSelect(choices=ECON_CHOICES, attrs={'id':'radioecon'}), label="Economic System")
    polsystem = forms.IntegerField(widget=forms.RadioSelect(choices=POL_CHOICES, attrs={'id':'radiopol'}), label="Political System")


class NewTradeForm(forms.Form):

    def __init__(self, millevel, *args, **kwargs):
        super(NewTradeForm, self).__init__(*args, **kwargs)

        reslist = [('0','GEU'),
                   ('1','Warpfuel'),
                   ('2','Duranium'),
                   ('3','Tritanium'),
                   ('4','Adamantium'),
                   ('11','Fighters'),
                   ('12','Corvettes'),
                   ('13','Light Cruisers'),
                   ('14','Destroyers'),
                   ('15','Frigates'),
                   ('16','Heavy Cruisers'),
                   ('17','Battlecruisers'),
                   ('18','Battleships'),
                   ('19','Dreadnoughts'),]

        if millevel < v.millevel('cor'):
            RESOURCE_CHOICES = reslist[:7]
        elif millevel < v.millevel('lcr'):
            RESOURCE_CHOICES = reslist[:8]
        elif millevel < v.millevel('des'):
            RESOURCE_CHOICES = reslist[:9]
        elif millevel < v.millevel('fri'):
            RESOURCE_CHOICES = reslist[:10]
        elif millevel < v.millevel('hcr'):
            RESOURCE_CHOICES = reslist[:11]
        elif millevel < v.millevel('bcr'):
            RESOURCE_CHOICES = reslist[:12]
        elif millevel < v.millevel('bsh'):
            RESOURCE_CHOICES = reslist[:13]
        else:
            RESOURCE_CHOICES = reslist

        self.fields["offer"] = forms.IntegerField(widget=forms.Select(choices=RESOURCE_CHOICES, attrs={'id':'offerres'}))
        self.fields["amountoff"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10', 'id':'offeramount'}), label="Amount")
        self.fields["receive"] = forms.IntegerField(widget=forms.Select(choices=RESOURCE_CHOICES))
        self.fields["amountrec"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10'}), label="Amount")
        self.fields["amounttrades"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10', 'id':'tradesamount', 'value':1}),
            label="No. of trades")


class ShipMoveForm(forms.Form):

    def __init__(self, world, *args, **kwargs):
        super(ShipMoveForm, self).__init__(*args, **kwargs)

        SHIP_CHOICES = utilities.formshiplist(world.millevel, list(shiplist), True)

        flagship = (None if world.flagshiptype == 0 else ('10','Personal Ship'))

        if flagship is not None:
            SHIP_CHOICES.append(flagship)

        self.fields["shiptype"] = forms.IntegerField(widget=forms.Select(choices=SHIP_CHOICES, attrs={'id':'shipmoveship'}), label="Ship Type")
        self.fields["amount"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10','id':'shipmoveamount'}), label="Amount")
        self.fields["regionfrom"] = forms.CharField(max_length=1, widget=forms.Select(choices=REGION_CHOICES), label="From")
        self.fields["regionto"] = forms.CharField(max_length=1, widget=forms.Select(choices=REGION_CHOICES), label="To")


class ShipMothballForm(forms.Form):

    def __init__(self, millevel, *args, **kwargs):
        super(ShipMothballForm, self).__init__(*args, **kwargs)

        SHIP_CHOICES = utilities.formshiplist(millevel, list(shiplist))

        self.fields["shiptype"] = forms.IntegerField(widget=forms.Select(choices=SHIP_CHOICES, attrs={'id':'mothballship'}), label="Ship Type")
        self.fields["amount"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10','id':'mothballamount'}), label="Amount")


class StagingForm(forms.Form):

    def __init__(self, millevel, *args, **kwargs):
        super(StagingForm, self).__init__(*args, **kwargs)

        SHIP_CHOICES = utilities.formshiplist(millevel, list(shiplist), True)

        self.fields["shiptype"] = forms.IntegerField(widget=forms.Select(choices=SHIP_CHOICES, attrs={'id':'mothballship'}), label="Ship Type")
        self.fields["amount"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10','id':'mothballamount'}), label="Amount")


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


class DirectAidForm(forms.Form):

    def __init__(self, ownmillevel, othermillevel, *args, **kwargs):
        super(DirectAidForm, self).__init__(*args, **kwargs)

        reslist = [('0','GEU'),
                   ('1','Warpfuel'),
                   ('2','Duranium'),
                   ('3','Tritanium'),
                   ('4','Adamantium'),
                   ('11','Fighters'),
                   ('12','Corvettes'),
                   ('13','Light Cruisers'),
                   ('14','Destroyers'),
                   ('15','Frigates'),
                   ('16','Heavy Cruisers'),
                   ('17','Battlecruisers'),
                   ('18','Battleships'),
                   ('19','Dreadnoughts'),]

        corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = utilities.levellist()

        if ownmillevel < corlevel or othermillevel < corlevel:
            RESOURCE_CHOICES = reslist[:7]
        elif ownmillevel < lcrlevel or othermillevel < lcrlevel:
            RESOURCE_CHOICES = reslist[:8]
        elif ownmillevel < deslevel or othermillevel < deslevel:
            RESOURCE_CHOICES = reslist[:9]
        elif ownmillevel < frilevel or othermillevel < frilevel:
            RESOURCE_CHOICES = reslist[:10]
        elif ownmillevel < hcrlevel or othermillevel < hcrlevel:
            RESOURCE_CHOICES = reslist[:11]
        elif ownmillevel < bcrlevel or othermillevel < bcrlevel:
            RESOURCE_CHOICES = reslist[:12]
        elif ownmillevel < bshlevel or othermillevel < bshlevel:
            RESOURCE_CHOICES = reslist[:13]
        else:
            RESOURCE_CHOICES = reslist

        self.fields["send"] = forms.IntegerField(widget=forms.Select(choices=RESOURCE_CHOICES, attrs={'id':'offerres'}))
        self.fields["amountsend"] = forms.IntegerField(widget=forms.NumberInput(attrs={'size':'10', 'id':'offeramount'}), label="Amount")


class GalaxySortForm(forms.Form):

    SORT_CHOICES = (
        ('worldid','ID, ascending'),
        ('-worldid','ID, descending'),
        ('gdp','GDP, ascending'),
        ('-gdp','GDP, descending'),
        ('world_name','World name, ascending'),
        ('-world_name','World name, descending'),
        ('user_name','Username, ascending'),
        ('-user_name','Username, descending'),
        ('warpoints','War points, ascending'),
        ('-warpoints','War points, descending'),
    )

    sortby = forms.CharField(max_length=20, widget=forms.Select(choices=SORT_CHOICES, attrs={'id':'sortselect'}), label="Sort By")


class ResearchForm(forms.Form):

    researchamount = forms.IntegerField(label="GEU Amount")


class RegistrationUniqueEmailCounters(regform):

    username = forms.RegexField(regex=r'^[\w.@+-]+$', max_length=30, label=_("Username"),
        error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")},
        widget=forms.TextInput(attrs={'class': 'countable', 'maxlength': '30',}))


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
            listlogs = WarLog.objects.filter(owner=world)

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

        TARGET_CHOICES = [(target.worldid, target.world_name) for target in listtargets]

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


class GDPSaleForm(forms.Form):

    buyer = forms.CharField(label="Buyer's World ID", max_length=10)
    geuamount = forms.IntegerField(label="GEU Amount")
    gdpamount = forms.IntegerField(label="GDP Amount")

    def clean_buyer(self):
        """Validates Buyer World ID"""
        data = self.cleaned_data['buyer']
        try:
            World.objects.get(worldid=data)
        except World.DoesNotExist:
            raise forms.ValidationError("Invalid World ID!")
        return data

    def clean_geuamount(self):
        """Validates GEU Amount Number"""
        data = self.cleaned_data['geuamount']
        if data < 0:
            raise forms.ValidationError("You cannot ask for a negative value!")
        return data

    def clean_gdpamount(self):
        """Validates GDP in Seller's world as well as value of form"""
        data = self.cleaned_data['gdpamount']
        if data < 0:
            raise forms.ValidationError("You cannot offer a negative value!")
        return data



