# Django Imports
from django.core.urlresolvers import reverse
from django.templatetags.static import static
import wawmembers.variables as v

'''
Text results from the outcomes of policies.
'''

##########
### SHARED
##########

def nomoney():
    return "You do not have enough money!"

def notenoughshipyards():
    return "You do not have enough free shipyards!"

def notenoughduranium():
    return "You do not have enough duranium!"

def notenoughtritanium():
    return "You do not have enough tritanium!"

def notenoughadamantium():
    return "You do not have enough adamantium!"

def needhigherlevel():
    return "Your military level is not advanced enough to refine these materials!"


############
### ECONOMIC
############

def toomuchgrowth():
    return "Your economy will not be able to support such high growth!"


def buildresource(result):
    if result == 'TooMany':
        message = "You are producing too much of your trade resource!"
    elif result == 'Success':
        message = "You have successfully increased the production of your trade resource!"
    return message


def noobgrowth(result):
    imgloc = static('wawmembers/cheap.gif')
    if result == 'TooRich':
        message = "Your world is too rich for cheap goods to have an effect on growth!"
    elif result == 'Success':
        message = """<img src="%s" alt="cheap"><br>Your world gains some growth off the back of cheap stuff.""" % imgloc
    return message


def buybonds(result):
    imgloc = static('wawmembers/buybonds.gif')
    if 50 < result <= 100:
        message = """<img src="%s" alt="buybonds"><br>Growth increases as your buying program drives up the supply of money.""" % imgloc
    elif 1 <= result <= 50:
        message = "Despite your buying program, the economy fails to grow."
    elif result == 'NotFreeorMixed':
        message = "You are a Central Planning world!"
    return message


def forcedlabour(result):
    imgloc = static('wawmembers/forcedlabour.gif')
    if 15 < result <= 100:
        message = """<img src="%s" alt="forcedlabour"><br>Growth increases as your dissenters are put to back-breaking work.""" % imgloc
    elif 10 < result <= 15:
        message = "Despite your harsh work hours, your dissenters do not manage to increase global growth."
    elif 1 <= result <= 10:
        message = "The dissenters escape and join the rebels!"
    elif result == 'NotDictatorship':
        message = "Only autocracies have enough dissenters to put to work!"
    elif result == 'StabilityTooLow':
        message = "Your stability is too low! You cannot risk a collapse of your rule!"
    return message


def nationalise(result):
    if result == 'NotFreeOrMixed':
        message = "You own all services already - there is nothing to nationalise!"
    elif result == 'Success':
        message = "Capitalism is a scourge! You seize businesses and investment."
    elif result == 'Already':
        message = "You have already changed economic system this turn!"
    return message


def privatise(result):
    if result == 'NotCPorMixed':
        message = "You have sold off all your state assets already - there is nothing to privatise!"
    elif result == 'Success':
        message = "The free market will fix everything! You sell off state assets."
    elif result == 'Already':
        message = "You have already changed economic system this turn!"
    return message


def buildfuelrefinery(result):
    imgloc = static('wawmembers/warpfuel.gif')
    if result == 'TooMany':
        message = "Your fleet engineers cannot build so many fuel refineries in one day!"
    elif result == 'Failure':
        message = "Unfortunately your refinery suffered a catastrophic failure when setting up."
    elif result == 'Success':
        message = """<img src="%s" alt="production"><br>Your refinery set up successfully! \
            <br>You gain 10 warpfuel per turn!""" % imgloc
    return message


def prospectduranium(result):
    imgloc = static('wawmembers/duranium.gif')
    if result == 'TooMany':
        message = "Your fleet engineers have searched all they can today for duranium."
    elif result == 'Failure':
        message = "Unfortunately your expedition failed to find any duranium-rich asteroids."
    elif result == 'Success':
        message = """<img src="%s" alt="production"><br>Your expedition found a suitable duranium-rich asteroid! \
            <br> You gain 3 duranium per turn.""" % imgloc
    return message


def prospecttritanium(result):
    imgloc = static('wawmembers/tritanium.gif')
    if result == 'TooMany':
        message = "Your fleet engineers have searched all they can today for tritanium."
    elif result == 'Failure':
        message = "Unfortunately your expedition failed to find any tritanium-rich asteroids."
    elif result == 'Success':
        message = """<img src="%s" alt="production"><br>Your expedition found a suitable tritanium-rich asteroid! \
            <br> You gain 2 tritanium per turn.""" % imgloc
    return message


def prospectadamantium(result):
    imgloc = static('wawmembers/adamantium.gif')
    if result == 'TooMany':
        message = "Your fleet engineers have searched all they can today for adamantium."
    elif result == 'Failure':
        message = "Unfortunately your expedition failed to find any adamantium-rich asteroids."
    elif result == 'Success':
        message = """<img src="%s" alt="production"><br>Your expedition found a suitable adamantium-rich asteroid! \
            <br> You gain 1 adamantium per turn.""" % imgloc
    return message


def salvagemission(result):
    from wawmembers.newsgenerator import salvagetext
    imgloc = static('wawmembers/salvage.gif')
    if result == 'NoSalvage':
        message = "There is no salvage for you to retrieve!"
    elif result == 'AlreadySalvaged':
        message = "You have already launched a salvage mission this turn!"
    else:
        message = """<img src="%s" alt="salvage"><br>Your salvage mission managed to return <br>\
            %s in useful materials.""" % (imgloc, salvagetext(result[0],result[1],result[2]))
    return message

prospecting = {
    'warpfuelprod': buildfuelrefinery,
    'duraniumprod': prospectduranium,
    'tritaniumprod': prospecttritanium,
    'adamantiumprod': prospectadamantium,
}

def shutdown(minetype):
    imgloc = static('wawmembers/closedmine.jpg')
    imgstr = '<img src="%s" alt="salvage"><br>' % imgloc
    result = minetype + (' refinery' if minetype == 'warpfuel' else ' mine')
    return "The workers are sad they have to find new jobs as your %s shuts down." % result


def nomines(minetype):
    adj = minetype + (' refinery' if minetype == 'warpfuel' else ' mine')
    return "Can't shut down another %s! They're all closed!" % adj

def reopen(minetype):
    adj = minetype + (' refinery' if minetype == 'warpfuel' else ' mine')
    imgstr = '<img src="%s" alt="salvage"><br>' % static('wawmembers/%s.gif' % minetype)
    return "%sThe workers are happy to be employed once more and are eager to resume working!" % imgstr


############
### DOMESTIC
############

def maxqol():
    message = "Your people's quality of life is already at the highest it can be!"
    return message


def arrest(result):
    imgloc = static('wawmembers/arrest.gif')
    if 95 < result <= 100:
        message = """<img src="%s" alt="arrest"><br>Some of the dissenters you arrested were collaborating<br> \
            with the rebels! Rebel strength decreases.""" % imgloc
    elif 1 <= result <= 95:
        message = """<img src="%s" alt="arrest"><br>You imprison your opponents,<br>\
            and the noise of dissent gets quieter.""" % imgloc
    elif result == 'ArrestedAll':
        message = "Your prisons are at full capacity!"
    return message


def free(result):
    imgloc = static('wawmembers/free.gif')
    if 80 < result <= 100:
        message = """<img src="%s" alt="free"><br> \
            Some of the dissidents you free go on to join<br>the rebels. Their strength has increased!""" % imgloc
    elif 1 <= result <= 80:
        message = """<img src="%s" alt="free"><br>Your clemency reflects well on your rule, which is<br> \
            seen as being more open. Perception increases!""" % imgloc
    elif result == 'FreedAll':
        message = "There are no dissenters to free!"
    return message


def martiallaw(result, timediff=None):
    from wawmembers.utilities import timedeltadivide
    imgloc = static('wawmembers/martiallaw.gif')
    if timediff != None:
        h, m, s = timedeltadivide(timediff)

    if result == 'NotAtWar':
        message = "You can only declare a global state of martial law in wartime."
    elif result == 'Dictator':
        message = "You refuse to give up your ultimate power to the Fleet Admiralty!"
    elif result == 'AlreadyAdmiralty':
        message = "The Fleet Admiralty is already in control of your world!"
    elif result == 'TooSoon':
        message = "You can only declare martial law once every 4 turns! You still have %s:%s:%s before you can re-declare." % (h, m, s)
    elif result == 'UnderTime':
        message = "None of your wars have been long enough to warrant declaring Martial Law! You still have %s:%s:%s \
            before you can enact this policy." % (h, m, s)
    elif result == 'Success':
        message = """<img src="%s" alt="arrest"><br>The Fleet Admiralty seizes control of your world as martial law<br> \
            is declared. You gain some of your best ships!""" % imgloc
    return message


def citybuilding(result):
    imgloc = static('wawmembers/city.gif')
    if 95 < result <= 100:
        message = """<img src="%s" alt="city"><br> \
            People flock to the new cities and their happiness<br> increases, as does their quality of life.""" % imgloc
    elif 1 <= result <= 95:
        message = """<img src="%s" alt="arrest"><br>People flock to the new cities and their happiness increases.""" % imgloc
    return message


def literacy():
    imgloc = static('wawmembers/reading.gif')
    message = """<img src="%s" alt="literacy"><br> \
        Your literacy program reaches many worldwide,<br>and people's quality of life increases as a result.""" % imgloc
    return message


def healthcare():
    imgloc = static('wawmembers/healthcare.gif')
    message = """<img src="%s" alt="healthcare"><br> \
        People's quality of life skyrockets as your healthcare<br>provisons reach millions around the globe.""" % imgloc
    return message


##############
### DIPLOMATIC
##############

def createfederation(result):
    if result == 'AlreadyAllied':
        message = "You cannot create an alliance if you are already part of one!"
    return message


def trainspy(result):
    imgloc = static('wawmembers/trainspy.gif')
    if result == 'TooMany':
        message = "You have sufficient spies already!"
    elif result == 'TooLong':
        message = "The name you have chosen is too long."
    elif result == 'Success':
        message = """<img src="%s" alt="trainspy"><br>Your intelligence agency immediately sets to work training a new spy.""" % imgloc
    return message


def gunrun(result):
    if result == 'NoTech':
        message = "You do not have enough research to give to the rebels!"
    return message


def sabotage(result):
    if result == 'NoFreeYards':
        message = "There are no empty shipyards you can destroy!"
    elif result == 'NoFuelProd':
        message = "There are no refineries you can destroy!"
    elif result == 'NoDurProd':
        message = "There are no duranium mines you can destroy!"
    elif result == 'NoTritProd':
        message = "There are no tritanium mines you can destroy!"
    elif result == 'NoAdamProd':
        message = "There are no adamantium mines you can destroy!"
    return message


def counterintel(result):
    imgloc = static('wawmembers/counterintel.gif')
    if result == 'NoSpies':
        message = "You have no spies at home!"
    elif result == 'NoneAvailable':
        message = "You have no spies available to conduct the counterintelligence sweep!"
    elif type(result) == list:
        if len(result) == 0:
            message = "Your sweep found nobody of interest."
        else:
            message = '<img src="%s" alt="counterintel"><br>' % imgloc
            for spy in result:
                linkworld = reverse('stats_ind', args=(spy.owner.worldid,))
                fullworld = '<a href="%(link)s">%(world)s</a>' % {'link':linkworld,'world':spy.owner.world_name}
                message += 'You caught and executed a spy named %s from the world of %s!<br>' % (spy.name, fullworld)
    return message


############
### MILITARY
############

def researchtext(world, incr):
    from wawmembers.utilities import levellist

    current = world.millevel
    total = world.millevel + incr
    progress1 = "Our scientists are considering the design principles for the new %s."
    progress2 = "Our scientists are researching a strong enough hull for the %s."
    progress3 = "Our scientists are producing propulsion and control systems for the %s."
    progress4 = "Our scientists are researching and producing the %s\'s armaments."
    progress5 = "Our scientists are producing the %s\'s sensors and other systems."
    progress6 = "Our scientists and the fleet engineer corps are running simulations and stress tests on the new %s."
    progress7 = "Our admirals and the fleet engineer corps are testing the new %s in a series of exercises."
    completed = "The new %s has been completed and is ready for production. Schematics have been sent to all shipyards!"
    corlevel, lcrlevel, deslevel, frilevel, hcrlevel, bcrlevel, bshlevel, drelevel = levellist()
    techrecieve = False
    if total < corlevel:
        if (total-0) > ((corlevel - 0)*90)/float(100):
            message = progress7 % 'corvette'
        elif (total-0) > ((corlevel - 0)*75)/float(100):
            message = progress6 % 'corvette'
        elif (total-0) > ((corlevel - 0)*60)/float(100):
            message = progress5 % 'corvette'
        elif (total-0) > ((corlevel - 0)*45)/float(100):
            message = progress4 % 'corvette'
        elif (total-0) > ((corlevel - 0)*30)/float(100):
            message = progress3 % 'corvette'
        elif (total-0) > ((corlevel - 0)*15)/float(100):
            message = progress2 % 'corvette'
        else:
            message = progress1 % 'corvette'
    elif (current < corlevel) and (current + incr >= corlevel):
        message = completed % 'corvette'
        techrecieve = "corvettes"

    elif total < lcrlevel:
        if (total-corlevel) > ((lcrlevel - corlevel)*90)/float(100):
            message = progress7 % 'light cruiser'
        elif (total-corlevel) > ((lcrlevel - corlevel)*75)/float(100):
            message = progress6 % 'light cruiser'
        elif (total-corlevel) > ((lcrlevel - corlevel)*60)/float(100):
            message = progress5 % 'light cruiser'
        elif (total-corlevel) > ((lcrlevel - corlevel)*45)/float(100):
            message = progress4 % 'light cruiser'
        elif (total-corlevel) > ((lcrlevel - corlevel)*30)/float(100):
            message = progress3 % 'light cruiser'
        elif (total-corlevel) > ((lcrlevel - corlevel)*15)/float(100):
            message = progress2 % 'light cruiser'
        else:
            message = progress1 % 'light cruiser'
    elif (current < lcrlevel) and (current + incr >= lcrlevel):
        message = completed % 'light cruiser'
        techrecieve = "light_cruisers"

    elif total < deslevel:
        if (total-lcrlevel) > ((deslevel - lcrlevel)*90)/float(100):
            message = progress7 % 'destroyer'
        elif (total-lcrlevel) > ((deslevel - lcrlevel)*75)/float(100):
            message = progress6 % 'destroyer'
        elif (total-lcrlevel) > ((deslevel - lcrlevel)*60)/float(100):
            message = progress5 % 'destroyer'
        elif (total-lcrlevel) > ((deslevel - lcrlevel)*45)/float(100):
            message = progress4 % 'destroyer'
        elif (total-lcrlevel) > ((deslevel - lcrlevel)*30)/float(100):
            message = progress3 % 'destroyer'
        elif (total-lcrlevel) > ((deslevel - lcrlevel)*15)/float(100):
            message = progress2 % 'destroyer'
        else:
            message = progress1 % 'destroyer'
    elif (current < deslevel) and (current + incr >= deslevel):
        message = completed % 'destroyer'
        techrecieve = "destroyers"

    elif total < frilevel:
        if (total-deslevel) > ((frilevel - deslevel)*90)/float(100):
            message = progress7 % 'frigate'
        elif (total-deslevel) > ((frilevel - deslevel)*75)/float(100):
            message = progress6 % 'frigate'
        elif (total-deslevel) > ((frilevel - deslevel)*60)/float(100):
            message = progress5 % 'frigate'
        elif (total-deslevel) > ((frilevel - deslevel)*45)/float(100):
            message = progress4 % 'frigate'
        elif (total-deslevel) > ((frilevel - deslevel)*30)/float(100):
            message = progress3 % 'frigate'
        elif (total-deslevel) > ((frilevel - deslevel)*15)/float(100):
            message = progress2 % 'frigate'
        else:
            message = progress1 % 'frigate'
    elif (current < frilevel) and (current + incr >= frilevel):
        message = completed % 'frigate'
        techrecieve = "frigates"

    elif total < hcrlevel:
        if (total-frilevel) > ((hcrlevel - frilevel)*90)/float(100):
            message = progress7 % 'heavy cruiser'
        elif (total-frilevel) > ((hcrlevel - frilevel)*75)/float(100):
            message = progress6 % 'heavy cruiser'
        elif (total-frilevel) > ((hcrlevel - frilevel)*60)/float(100):
            message = progress5 % 'heavy cruiser'
        elif (total-frilevel) > ((hcrlevel - frilevel)*45)/float(100):
            message = progress4 % 'heavy cruiser'
        elif (total-frilevel) > ((hcrlevel - frilevel)*30)/float(100):
            message = progress3 % 'heavy cruiser'
        elif (total-frilevel) > ((hcrlevel - frilevel)*15)/float(100):
            message = progress2 % 'heavy cruiser'
        else:
            message = progress1 % 'heavy cruiser'
    elif (current < hcrlevel) and (current + incr >= hcrlevel):
        message = completed % 'heavy cruiser'
        techrecieve = "heavy_cruisers"

    elif total < bcrlevel:
        if (total-hcrlevel) > ((bcrlevel - hcrlevel)*90)/float(100):
            message = progress7 % 'battlecruiser'
        elif (total-hcrlevel) > ((bcrlevel - hcrlevel)*75)/float(100):
            message = progress6 % 'battlecruiser'
        elif (total-hcrlevel) > ((bcrlevel - hcrlevel)*60)/float(100):
            message = progress5 % 'battlecruiser'
        elif (total-hcrlevel) > ((bcrlevel - hcrlevel)*45)/float(100):
            message = progress4 % 'battlecruiser'
        elif (total-hcrlevel) > ((bcrlevel - hcrlevel)*30)/float(100):
            message = progress3 % 'battlecruiser'
        elif (total-hcrlevel) > ((bcrlevel - hcrlevel)*15)/float(100):
            message = progress2 % 'battlecruiser'
        else:
            message = progress1 % 'battlecruiser'
    elif (current < bcrlevel) and (current + incr >= bcrlevel):
        message = completed % 'battlecruiser'
        techrecieve = "battlecruisers"

    elif total < bshlevel:
        if (total-bcrlevel) > ((bshlevel - bcrlevel)*90)/float(100):
            message = progress7 % 'battleship'
        elif (total-bcrlevel) > ((bshlevel - bcrlevel)*75)/float(100):
            message = progress6 % 'battleship'
        elif (total-bcrlevel) > ((bshlevel - bcrlevel)*60)/float(100):
            message = progress5 % 'battleship'
        elif (total-bcrlevel) > ((bshlevel - bcrlevel)*45)/float(100):
            message = progress4 % 'battleship'
        elif (total-bcrlevel) > ((bshlevel - bcrlevel)*30)/float(100):
            message = progress3 % 'battleship'
        elif (total-bcrlevel) > ((bshlevel - bcrlevel)*15)/float(100):
            message = progress2 % 'battleship'
        else:
            message = progress1 % 'battleship'
    elif (current < bshlevel) and (current + incr >= bshlevel):
        message = completed % 'battleship'
        techrecieve = "battleships"

    elif total < drelevel:
        if (total-bshlevel) > ((drelevel - bshlevel)*90)/float(100):
            message = progress7 % 'dreadnought'
        elif (total-bshlevel) > ((drelevel - bshlevel)*75)/float(100):
            message = progress6 % 'dreadnought'
        elif (total-bshlevel) > ((drelevel - bshlevel)*60)/float(100):
            message = progress5 % 'dreadnought'
        elif (total-bshlevel) > ((drelevel - bshlevel)*45)/float(100):
            message = progress4 % 'dreadnought'
        elif (total-bshlevel) > ((drelevel - bshlevel)*30)/float(100):
            message = progress3 % 'dreadnought'
        elif (total-bshlevel) > ((drelevel - bshlevel)*15)/float(100):
            message = progress2 % 'dreadnought'
        else:
            message = progress1 % 'dreadnought'

    elif (current < drelevel) and (current + incr >= drelevel):
        message = completed % 'dreadnought'
        techrecieve = "dreadnoughts"
    if techrecieve:
        next_tier = v.shipindices.index(techrecieve) - 1
        world.techlevel = v.tiers[next_tier]
        world.save(update_fields=['techlevel'])
        world.preferences.recievefleet.__dict__[techrecieve] += 1
        world.preferences.recievefleet.save(update_fields=[techrecieve])
    return message


def research(outcome, result=None):
    imgloc = static('wawmembers/research.gif')
    if outcome == 'TooSoon':
        message = "You cannot order research again this turn - your scientists are still working!"
    elif outcome == 'TooMuch':
        message = "Your scientists cannot work through so much funding!"
    elif outcome == 'NoDur':
        message = "You do not have enough duranium to commence research!"
    elif outcome == 'NoTrit':
        message = "You do not have enough tritanium to commence research!"
    elif outcome == 'NoAdam':
        message = "You do not have enough adamantium to commence research!"
    elif outcome == 'Success':
        message = """<img src="%s" alt="research"><br>%s""" % (imgloc, result)
    return message


def shipyards(outcome):
    imgloc = static('wawmembers/research.gif')
    if outcome == 'Success':
        message = """<img src="%s" alt="shipyard"><br>Your engineers quickly construct an orbital shipyard and put it into service.""" % imgloc
    return message


def freighters(outcome, amount):
    imgloc = static('wawmembers/freighter.gif')
    from wawmembers.utilities import plural
    if outcome == 'Success':
        multiple = ('%s ' % amount if amount > 0 else '')
        message = """<img src="%s" alt="freighter"><br>Your fleet engineers get to work building your %s%s in the shipyards.""" \
          % (imgloc, multiple, plural('freighter', amount))
    return message


def training(outcome):
    imgloc = static('wawmembers/training.gif')
    if outcome == 'AtMax':
        message = "Your fleet is already at maximum training!"
    elif outcome == 'Success':
        message = """<img src="%s" alt="training"><br>Your fleet carries out its drills and there is<br> \
            visible improvement in their tactics and cohesion!""" % imgloc
    return message


def startshipbuild(shiptype, amount):
    from wawmembers.utilities import resname
    name = resname(shiptype+10, amount, lower=True)
    return 'You start construction of %s %s.' % (amount, name)


def norebels():
    return "There are no rebels to attack!"


def personalship(outcome, shiptype=None):
    from wawmembers.display import personalshipname
    name = (None if shiptype == None else personalshipname(shiptype))

    if outcome == 'Already':
        message = 'You already have a personal ship!'
    elif outcome == 'Success':
        message = 'You start construction of a %s.' % name

    return message
