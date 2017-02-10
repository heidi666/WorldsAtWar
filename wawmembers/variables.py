# Django Imports
from django.utils.timezone import utc
from django.templatetags.static import static

# Python Imports
import datetime as time
import random

# Maintenance Mode
maintenance = True # True for maintenance - don't change this

'''
Misc variables and simple functions used in a lot of place                           s.
'''

origcorlevel = 5000
origlcrlevel = 30000
origdeslevel = 95000
origfrilevel = 230000
orighcrlevel = 460000
origbcrlevel = 820000
origbshlevel = 1400000
origdrelevel = 2200000

# Military levels
def millevel(key):
    from wawmembers.models import GlobalData
    millevels = GlobalData.objects.get(pk=1)
    if key == 'cor':
        return millevels.corlevel
    elif key == 'lcr':
        return millevels.lcrlevel
    elif key == 'des':
        return millevels.deslevel
    elif key == 'fri':
        return millevels.frilevel
    elif key == 'hcr':
        return millevels.hcrlevel
    elif key == 'bcr':
        return millevels.bcrlevel
    elif key == 'bsh':
        return millevels.bshlevel
    elif key == 'dre':
        return millevels.drelevel


eventfighters = 10 #amount of fighters you get from noob event


# Resources
#for ordered looping
productionindices = ['warpfuelprod', 'duraniumprod', 'tritaniumprod', 'adamantiumprod']

production = { #amount of resources per mine
    'warpfuelprod': {'cost': 750, 'production': 10, 'chance': 5},
    'duraniumprod': {'cost': 1200, 'production': 5, 'chance': 40},
    'tritaniumprod': {'cost': 1550, 'production': 3, 'chance': 50},
    'adamantiumprod': {'cost': 2100, 'production': 1, 'chance': 70},
}

resources = ['budget', 'warpfuel', 'duranium', 'tritanium', 'adamantium']

# Ship indexes
shipindices = ['freighters', 'fighters','corvettes','light_cruisers','destroyers','frigates','heavy_cruisers','battlecruisers','battleships','dreadnoughts']
tiers = ['Fighter','Corvette','Light cruiser','Destroyer','Frigate','Heavy cruiser','Battlecruiser','Battleship','Dreadnought']

tradenames = ['Currency', 'Warpfuel', 'Duranium', 'Tritanium', 'Adamantium', 'Freighters', 'Fighters', 'Corvettes', 'Light Cruisers', 'Destroyers',
                  'Frigates', 'Heavy Cruisers', 'Battlecruisers', 'Battleships', 'Dreadnoughts']

#underscore in lieu of spaces, otherwise fleet model can't use them

training_costs = {
    'fighters': 1,
    'corvettes': 2,
    'light_cruisers': 4,
    'destroyers': 6,
    'frigates': 8,
    'heavy_cruisers': 12,
    'battlecruisers': 18,
    'battleships': 30,
    'dreadnoughts': 50
}

bonuses = { #for easy game balance alteration
    'amyntas': 1.2,
    'bion': 0.80,
    'cleon': 0.75,
    'draco': 0.75,
}

#increment this every time a field is added to the fleet model
#using a global variable is easier than editing all the code calling _meta.fields
fleetindex = 9
# Background selection
def background():
    return random.randint(1,10)

#dict of the amount of space each resources takes up
freighter_capacity = {
    'total': 1000, #total cargo space
    'warpfuel': 4,
    'duranium': 15,
    'tritanium': 25,
    'adamantium': 30,
    'gdp': 0,
    'growth': 0,
    'blueprints': 1,
}

# Comm display preference
commprefs = ['new','old']

# Comm spam denial
delay = 10 
commlimit = 2
#$commlimit comms per $delay seconds   

fuelupkeep = 0.1

# Sectors
sectors = ['amyntas','bion','cleon','draco']

# Galaxy sort preference
galsortprefs = ['worldid','-worldid','gdp','-gdp','world_name','-world_name','user_name','-user_name','warpoints','-warpoints']

# Ship sort prefs
stagingprefs = ['prodhome', 'prodstaging', 'sendhome', 'sendstaging', 'receivehome', 'receivestaging']

# Alliance stats display
alliancestatprefs = ['leadergeneral', 'officergeneral', 'membergeneral', 'publicgeneral',
    'leadereconomic', 'officereconomic', 'membereconomic', 'publiceconomic',
    'leaderresources', 'officerresources', 'memberresources', 'publicresources',
    'leadermilitary', 'officermilitary', 'membermilitary', 'publicmilitary',
    'leaderecontypes', 'officerecontypes', 'memberecontypes', 'publicecontypes',
    'leaderpoltypes', 'officerpoltypes', 'memberpoltypes', 'publicpoltypes',
    'leadermillevels', 'officermillevels', 'membermillevels', 'publicmillevels']

# Policy prefs
policyprefs = ['js', 'econ', 'domestic', 'diplomacy', 'military']

# Build prefs
buildprefs = ['ind', 'multi']

#keys map to model fields
upkeep = {
    'warpfuelprod': 2,
    'duraniumprod': 15,
    'tritaniumprod': 25,
    'adamantiumprod': 40
}

mildis = {
    'freighters': 'Freighters'
}


def shipcosts(region=False):
    costs = {
    'freighters': {
        'geu': 100,
        'duranium': 5,
        'tritanium': 0,
        'adamantium': 0,
        'productionpoints': 4,
        'fuel': 0,
        'firepower': 0,
        'damage': 0,
        'research': {'duranium': None}
    },
    'fighters': {
        'geu': 50,
        'duranium': 1,
        'tritanium': 0,
        'adamantium': 0,
        'productionpoints': 1,
        'fuel': 1,
        'firepower': 1,
        'damage': 1,
        'research': {'duranium': None}
    },
    'corvettes': {
        'geu': 100,
        'duranium': 5,
        'tritanium': 0,
        'adamantium': 0,
        'productionpoints': 4,
        'fuel': 2,
        'firepower': 5,
        'damage': 5,
        'research': {'duranium': 2}
    },
    'light_cruisers': {
        'geu': 200,
        'duranium': 10,
        'tritanium': 0,
        'adamantium': 0,
        'productionpoints': 6,
        'fuel': 3,
        'firepower': 10,
        'damage': 10,
        'research': {'duranium': 4}
    },
    'destroyers': {
        'geu': 300,
        'duranium': 15,
        'tritanium': 5,
        'adamantium': 0,
        'productionpoints': 12,
        'fuel': 4,
        'firepower': 15,
        'damage': 15,
        'research': {'duranium': 8, 'tritanium': 2}
    },
    'frigates': {
        'geu': 400,
        'duranium': 20,
        'tritanium': 10,
        'adamantium': 0,
        'productionpoints': 24,
        'fuel': 5,
        'firepower': 20,
        'damage': 20,
        'research': {'duranium': 12, 'tritanium': 4}
    },
    'heavy_cruisers': {
        'geu': 500,
        'duranium': 25,
        'tritanium': 15,
        'adamantium': 0,
        'productionpoints': 40,
        'fuel': 6,
        'firepower': 25,
        'damage': 25,
        'research': {'duranium': 16, 'tritanium': 8}
    },
    'battlecruisers': {
        'geu': 600,
        'duranium': 30,
        'tritanium': 20,
        'adamantium': 5,
        'productionpoints': 72,
        'fuel': 8,
        'firepower': 30,
        'damage': 30,
        'research': {'duranium': 20, 'tritanium': 12, 'adamantium': 2}
    },
    'battleships': {
        'geu': 800,
        'duranium': 35,
        'tritanium': 25,
        'adamantium': 10,
        'productionpoints': 180,
        'fuel': 10,
        'firepower': 35,
        'damage': 35,
        'research': {'duranium': 25, 'tritanium': 15, 'adamantium': 5}
    },
    'dreadnoughts': {
        'geu': 1000,
        'duranium': 40,
        'tritanium': 30,
        'adamantium': 20,
        'productionpoints': 480,
        'fuel': 15,
        'firepower': 40,
        'damage': 40,
        'research': {'duranium': 30, 'tritanium': 20, 'adamantium': 10}
    }, 
    }


    if region == 'bion':
        for key, value in costs.iteritems():
            value['geu'] *= 0.85
            value['duranium'] *=int(round(value['duranium'] * 0.8))
            value['tritanium'] *=int(round(value['tritanium'] * 0.8))
            value['adamantium'] *=int(round(value['adamantium'] * 0.8))
            value['productionpoints'] *=int(round(value['productionpoints'] * 0.9))
    return costs


#Current time
def now():
    return time.datetime.utcnow().replace(tzinfo=utc)

def nowplusweek():
    return now() + time.timedelta(weeks=1)

# Data when signing up
regiondata = [
    '<td align="center" style="width:25%%"><img src="%s" alt="Amyntas"></td> \
        <td style="width:60%%">Amyntas lies on the most heavily trafficked trade routes of the galaxy: worlds here will earn money faster than \
        other sectors. <br> <span style="color:green;">Bonus: +20%% to income.</span></td>' % static('wawmembers/amyntas.png'),
    '<td align="center"><img src="%s" alt="Bion"></td> \
        <td>The forges and shipyards in Bion are the most efficient in the galaxy: worlds here will produce ships cheaper \
        than other sectors. <br> <span style="color:green;">Bonus: Cheaper ships (15%% cost, 20%% resources).</span></td>'
        % static('wawmembers/bion.png'),
    '<td align="center"><img src="%s" alt="Cleon"></td> \
        <td>An abundance of asteroids permeates every system in Cleon: worlds here will have no problem finding an abundance of resources \
        in their system. <br> <span style="color:green;">Bonus: +30%% chance to finding resources, -10%% increase on mine price.</span></td>'
        % static('wawmembers/cleon.png'),
    '<td align="center"><img src="%s" alt="Draco"></td> \
        <td>Draco holds the honour of being the most technologically advanced sector: worlds here will find their research progresses \
        much faster. <br> <span style="color:green;">Bonus: +25%% to research progress. 20%% initial spy skill.</span></td>'
        % static('wawmembers/draco.png'),
    ]

econdata = [
    '<td>A free market world draws its economic strength from open trade. You will depend on interaction with other worlds to achieve your \
        growth, but it will be cheap and plentiful.</td>',
    '<td>A mixed economy world treads the line between being a capitalistic paradise and a command economy. It will receive smaller \
        disadvantages from each, but also smaller advantages.</td>',
    '<td>A central planning world has an economy based upon hard work and productivity. You will be less dependent on other worlds for growth, \
        but you will still be able to tax any trade routes you set up.</td>',
    ]

poldata = [
    '<td>A liberal democracy is free and open. The stability of your world will depend almost entirely on how popular you are with \
        the people and will be cheaper to maintain.</td>',
    '<td>A totalitarian democracy, while elected, exerts much greater control on the people. Stability will depend \
        less on the people\'s approval and more on their quality of life.</td>',
    '<td>A world under single-party rule will receive random events raising their attributes. Stability will depend \
        equally on the people\'s perception of you and their quality of life.</td>',
    '<td>A fleet admiralty world is geared almost entirely towards military endeavours. You will get random events that raise your \
        military attributes. Stability will depend more on quality of life than approval.</td>',
    '<td>An autocracy holds ultimate control over the people. As such you can use forced labour, a free option to raise your growth. \
        Stability will depend almost entirely on the people\'s quality of life.</td>',
    ]

# Comm for new worlds
introcomm = "Welcome to Worlds at War 5!"

# Donator list
donorlist = [
'Argentina', 'YeshuaChrist', 'dissonanz', 'Big Willy', 'Genghis Khan',
'Ept2415', 'CommyWommy', 'DrKourin', 'Bilbo_Swaggins',
'Admiral_Parangosky', 'Slim', 'dable', 'Reagan', 'Rampagingwalrus', 'Caesar', 'niko', 'S37H',
'Kronos', 'Proditor', 'FinalSolution', 'Frank_Underwood', 'InfantImpaler', 'Kamakazi_Sunshine',
'Bubblegum', 'Crontical', 'Lykos', 'taikuh', 'Cotton', ' Ashe', 'Reuenthal', 'Clarissa', 'Crusader1488', 
'Whiskertoes', 'amazinglyaverage', 'Mengele-chan', 'Karazian', 'Lunin', 'cyrussteel', 'Noxmillien',
'Obersturmbannfuhrer', 'FlawedFlock', 'Uther_Fudreim', 'Speckled_Jim', 'Tibus_Heth', 'Joseph-Stalin',
]
# Rumsoddium messages
rumsodeconomy = 'The ritual worked perfectly. The pieces of rumsoddium glowed gently in the radio waves at first, but grew ' + \
    'brighter and brighter until a green beam shot out above the tetrahedron, punching a hole in the roof. The entire ' + \
    'atmosphere glowed a bright green for a minute or two, and as your citizens stood in awe, everywhere around the world ' + \
    'economic output increased twofold, and resources stored in warehouses doubled in quantity. You did have to shell out ' + \
    '10 GEU to repair the roof of your super secret installation where the ritual was carried out though.'

rumsodmilitary = 'The ritual worked perfectly. The pieces of rumsoddium glowed brightly as the X-rays bombarded them, and green ' + \
    'steam rose above them. A shimmering was observed above the square, which your scientists at first thought was merely ' + \
    'due to heat, but as it grew more intense they realised it was a distortion in spacetime. It was at this point your two ' + \
    'virgins ran out of the room as fast as they could. Your scientists were were about to shut the experiment down ' + \
    'when suddenly the room glowed a bright green, blinding all who observed. The next they looked, there was nothing in ' + \
    'the room. News reached your fleet\'s ears soon after about the terrible solar flares that knocked out a huge proportion ' + \
    'of your enemy\'s electronics, and burned warehouses wherever they were. Their economic output and resources must be halved!'
