# Django Imports
from django.utils.timezone import utc
from django.templatetags.static import static

# Python Imports
import datetime as time
import random

# Maintenance Mode
maintenance = True # True for maintenance - don't change this

'''
Misc variables and simple functions used in a lot of places.
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

# Resources
resources = [0,1,2,3,4,11,12,13,14,15,16,17,18,19]

# Ship indexes
shipindices = ['Fighters','Corvettes','Light Cruisers','Destroyers','Frigates','Heavy Cruisers','Battlecruisers','Battleships','Dreadnoughts']

# Background selection
def background():
    return random.randint(1,10)

# Comm display preference
commprefs = ['new','old']

# Sectors
sectors = ['A','B','C','D']

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

# Shipbuild costs
def matcosts(shiptype):
    if shiptype == 1:
        return 1, 0, 0
    elif shiptype == 2:
        return 5, 0, 0
    elif shiptype == 3:
        return 10, 0, 0
    elif shiptype == 4:
        return 15, 5, 0
    elif shiptype == 5:
        return 20, 10, 0
    elif shiptype == 6:
        return 25, 15, 0
    elif shiptype == 7:
        return 30, 20, 5
    elif shiptype == 8:
        return 35, 25, 10
    elif shiptype == 9:
        return 40, 30, 20

def shipcosts(region, shiptype):
    'Return cost, dur, trit, adam, shipyards, hours, fuel.'
    if shiptype == 1:
        cost, shipyards, hours, fuel = 50, 1, 1, 1
    elif shiptype == 2:
        cost, shipyards, hours, fuel = 100, 2, 2, 2
    elif shiptype == 3:
        cost, shipyards, hours, fuel = 200, 2, 3, 3
    elif shiptype == 4:
        cost, shipyards, hours, fuel = 300, 3, 4, 4
    elif shiptype == 5:
        cost, shipyards, hours, fuel = 400, 4, 6, 5
    elif shiptype == 6:
        cost, shipyards, hours, fuel = 500, 5, 8, 6
    elif shiptype == 7:
        cost, shipyards, hours, fuel = 600, 6, 12, 8
    elif shiptype == 8:
        cost, shipyards, hours, fuel = 800, 10, 18, 10
    elif shiptype == 9:
        cost, shipyards, hours, fuel = 1000, 20, 24, 15

    dur, trit, adam = matcosts(shiptype)

    if region == 'B':
        cost *= 0.85
        dur = int(round(dur*0.8))
        trit = int(trit*0.8)
        adam = int(adam*0.8)

    return cost, dur, trit, adam, shipyards, hours, fuel

# Industrial Program
def inddetails(world):
    'Variables for industrial program.'
    if world.econsystem == 0:
        indcap = 1200
        indcost = 80
    elif world.econsystem == -1:
        indcap = 2400
        indcost = 60
    else:
        indcap = 0
        indcost = 'N/A'
    return indcap, indcost

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
introcomm = "Welcome to Worlds at War! A comprehensive guide is here: http://wawgame.eu/guide " + \
    "(though it's a lot easier than it looks!), and rules for the game and forums are here: http://wawgame.eu/rules. " + \
    "Please do visit the forums, you'll enjoy the game a lot more if you participate in the metagame. " + \
    "As an encouragement you get a small in-game bonus if you post here: http://wawgame.eu/forums/index.php?topic=5282. " + \
    "Finally, many thanks for trying the game out! I hope you enjoy yourself and stick around. - heidi"

# Donator list
donatorlist = [1, 5, 7, 10, 11, 23, 25, 33, 37, 39, 41, 55, 56, 59, 66, 70, 77, 106, 127, 144, 191, 192, 193, 215, 230, 246, 324,
    367, 379, 384, 391, 411, 436, 441, 514, 612, 614, 617, 685, 733, 786, 907, 915, 972, 1060, 1107, 1111, 1250, 1573, 1643, 1721,
    1808, 1826, 2043, 2172, 2302, 2323, 2341, 2348, 2378, 3091, 3138, 3142, 3156, 3168, 3205, 3229, 3274, 3279, 3281, 3305, 3383,
    3471, 3475, 3508, 3550, 3578, 3886]

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
