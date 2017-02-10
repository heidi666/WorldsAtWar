# Django Imports
from django.core.urlresolvers import reverse
from django.templatetags.static import static

# WaW Imports
import wawmembers.variables as v
from wawmembers.utilities import plural as pl
import wawmembers.utilities as utilities

'''
HTML generation for news items.
'''


hl = '<p class="halfline">&nbsp;</p>'

##############
### RUMSODDIUM
##############

def rumsoddium(world):
    linkworld = reverse('stats_ind', args=(world.pk,))
    fullworld = '<a href="%s">%s</a>' % (linkworld, world.name)

    return "%s seized your prized rumsoddium after defeating you in your war!" % fullworld


def rumsodmilitaryreceive(world):
    linkworld = reverse('stats_ind', args=(world.pk,))
    fullworld = '<a href="%s">%s</a>' % (linkworld, world.name)

    return "Vicious storms by gigantic solar flares lashed your world, burning warehouses and electronics wherever they " + \
        "were, no matter how shielded. After the storms passed you ordered a thorough damage report, and were horrified to " + \
        "find that so many of your electronics were burned that your economic output must be halved! Your warehouses fared no " + \
        "better either, with approximately half of your resources lost. It will surely take months to recover! Through the exultant " + \
        "taunting your world receives from just about every passer-by, you discover that it was %s to visit this calamity upon you." % fullworld


#############
### ALLIANCES
#############

def allianceinvite(alliance, inviter):
    linkalliance = reverse('alliances_ind', args=(alliance.pk,))
    linkinviter = reverse('stats_ind', args=(inviter.pk,))

    fullalliance = '<a href="%s">%s</a>' % (linkalliance, alliance.alliance_name)
    fullinviter = '<a href="%s">%s</a>' % (linkinviter, inviter.name)

    status = ('leader' if inviter.leader else 'officer')

    return "You have been invited to the federation %(alliance)s by their %(status)s, %(inviter)s! Go to their federation page to accept." \
        % {'alliance':fullalliance, 'status':status, 'inviter':fullinviter}


def withdrawalmade(officer, amount):
    linkofficer = reverse('stats_ind', args=(officer.pk,))

    fullofficer = '<a href="%s">%s</a>' % (linkofficer, officer.name)

    return "%(amount)s GEUs have been withdrawn from your federation bank by your officer %(officer)s." \
        % {'amount':amount, 'officer':fullofficer}


def depositmade(member, amount):
    linkmember = reverse('stats_ind', args=(member.pk,))

    fullmember = '<a href="%s">%s</a>' % (linkmember, member.name)

    return "%(amount)s GEUs have been deposited to your federation bank by your member %(member)s." \
        % {'amount':amount, 'member':fullmember}


def officerdemotion():
    return "You have been demoted from officership in your federation!"


def memberpromotion():
    return "You have been promoted to officership in your federation!"


def purge(alliance):
    linkalliance = reverse('alliances_ind', args=(alliance.pk,))
    fullalliance = '<a href="%s">%s</a>' % (linkalliance, alliance.alliance_name)

    return "You have been expelled from the federation %s!" % fullalliance


def resignation(officer):
    linkofficer = reverse('stats_ind', args=(officer.pk,))

    fullofficer = '<a href="%s">%s</a>' % (linkofficer, officer.name)

    return "Your officer %s has resigned in your alliance!" % fullofficer


def successor(leader):
    linkleader = reverse('stats_ind', args=(leader.pk,))

    fullleader = '<a href="%s">%s</a>' % (linkleader, leader.name)

    return "%s, the leader of your alliance, has resigned and given you command!" % fullleader


#######
### WAR
#######

def wardec(world,reason):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return "%s has declared war on you! They gave the following reason: <i>%s</i>." % (fullworld,reason)

#format a fleet of losses into a string for easy display
def losses(shiplist):
    lostships = []
    for ship in list(shiplist._meta.fields)[v.fleetindex:]:
        if shiplist.__dict__[ship.name] > 0:
            lostships.append([ship.name, shiplist.__dict__[ship.name]])
    if len(lostships) == 0:
        return ' no ships at all'
    return utilities.resource_text(lostships)
    for entry in lostships:
        if shiplist.__dict__[entry] > 1: #we plural by default
            prettylost.append(entry.replace('_', ' '))
        else:
            prettylost.append(entry.replace('_', ' ')[:-1]) #strip off the 's' if == 1
    if len(lostships) == 1:
        return '%s %s' % (shiplist.__dict__[lostships[0]], prettylost[0])
    change = lostships[len(lostships) - 2]
    stop = lostships[len(lostships) - 1]
    for ship, text in zip(lostships, prettylost):
        if ship == change:
            lossadd = "%s %s and " % (shiplist.__dict__[ship], text)
        elif ship == stop:
            lossadd = "%s %s." % (shiplist.__dict__[ship], text)
        else:
            lossadd = "%s %s, " % (shiplist.__dict__[ship], text)
        loss += lossadd
    return loss


def tablelosses(targetlosses, worldlosses):
    index = 1
    table = '<table width="60%" class="striped supplydisplay"><tr class="verydark"><b><td class="hidden nohl"></td>\
        <td class="green center">We destroyed</td><td class="red center">We lost</td></b></tr>'

    thighest = utilities.highesttier(targetlosses)
    if v.shipindices.index(thighest) > v.shipindices.index(utilities.highesttier(worldlosses)):
        highest = thighest
    else:
        highest = utilities.highesttier(worldlosses)
    i = 1
    for ship in v.shipindices[1:v.shipindices.index(highest)+1]:
        table += '<tr class="%s"><td class="leftpad">%s</td><td class="center">%s</td><td class="center">%s</td></tr>' \
          % (('light' if not i % 2 else 'dark'), ship.capitalize().replace('_', ' '), targetlosses.__dict__[ship], worldlosses.__dict__[ship])
        i += 1
    table += '</table>'
    return table


def flagshipoutcome(flagmeet, flagworldlose, flagtargetlose):
    'Returns text outcome for flagships in war.'
    if flagmeet:
        init = '%s Your two flagships met amidst the battle turmoil, and a fierce battle ensued.<br>' % hl
        if flagworldlose and flagtargetlose:
            worldreport = targetreport = init + 'Unfortunately, our flagship was <span class="red">critically damaged</span>, but not before \
              <span class="green">destroying</span> the enemy\'s! <br> Both leaders escaped in rescue pods. <br> The people are \
              <span class="red">dismayed</span> to see the flagship destroyed, but <span class="green">happy</span> that the enemy\'s is too.'
        elif not flagworldlose and not flagtargetlose:
            worldreport = targetreport = init + 'Despite a few blows being exchanged, no lasting damage was done to either ship.'
        else:
            won = init + 'We struck a glorious blow and <span class="green">destroyed</span> their flagship! Their leader managed to \
              escape in a rescue pod. <br> Contentment <span class="green">rises</span> at home as they hear of this victory!'
            lost = init + 'Unfortunately, our flagship was <span class="red">destroyed</span> in the engagement, but you luckily escaped \
              in a rescue pod. <br> However, the people are <span class="red">dismayed</span> at home as they hear of this defeat.'
            if flagworldlose:
                worldreport = lost
                targetreport = won
            elif flagtargetlose:
                worldreport = won
                targetreport = lost
    else:
        if not flagworldlose and not flagtargetlose:
            worldreport = targetreport = ''
        else:
            won = '%s Our fleet struck a grievious blow, swarming the enemy flagship and <span class="green">destroying</span> it! \
              Their leader escaped in a rescue pod. <br> Contentment <span class="green">rises</span> at home as they hear of this victory!' % hl
            lost = '%s Terrible news! Their fleet swarmed our flagship, and it eventually was <span class="red">destroyed</span> in the face \
              of such punishment. <br> Luckily you managed to escape in a rescue pod. <br> However, the people are \
              <span class="red">dismayed</span> at home as they hear of this defeat.' % hl
            if flagworldlose:
                worldreport = lost
                targetreport = won
            elif flagtargetlose:
                worldreport = won
                targetreport = lost

    return worldreport, targetreport


def battleresult(sector, world, target, worldloss, targetloss, fleets, defensefleets, flag):
    #passes the flagship name if the flagship is in play in any of the involved fleets
    worldfleetstring = fleetnames(fleets, (flag['worldname'] if flag['world'] else False)) 
    targetfleetstring = fleetnames(defensefleets, (flag['targetname'] if flag['target'] else False))
    worldreport, targetreport = flagshipoutcome(flag['meet'], flag['worldloss'], flag['targetloss'])
    targetlink = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    worldlink = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    wfplural = ('s' if len(fleets) > 1 else '')
    tfplural = ('s' if len(defensefleets) > 1 else '')
    table = tablelosses(targetloss, worldloss)

    dataatt = "<b>Our %s engaged %s of world %s in %s! \
        %s Battle Report: %s </b> %s %s" \
          % (worldfleetstring, targetfleetstring, targetlink, sector, hl, hl, table, worldreport)
    wlosses = losses(worldloss)
    defenselosses = losses(targetloss)
    conj = 'and <span class="green">destroyed</span>'
    if wlosses == ' no ships at all' and defenselosses == ' no ships at all':
        mod = desc = ''
    elif wlosses == ' no ships at all':
        mod = ''
        desc = 'crushingly '
    elif defenselosses == ' no ships at all':
        mod = 'mighty'
        desc = 'pathetically '
    else:
        mod = desc = ''
        conj = 'but we managed to <span class="green">destroy</span>'

    datadef = "Your %s fleet%s <i>%s</i> was %sattacked by fleet%s <i>%s</i> \
        of world %s in %s! %s We <span class=\"red\">lost</span> %s in the resulting conflict, %s %s \
        in retaliation! %s" \
          % (mod, tfplural, targetfleetstring, desc, wfplural, worldfleetstring, worldlink, sector, hl, \
            defenselosses, conj, wlosses, targetreport)

    return dataatt, datadef

def fleetnames(fleets, flaginfo):
    flen = len(fleets)
    fleetstring = ('fleets ' if flen > 1 else 'fleet ')
    if flen == 0:
        fleetstring = ''
    for index, ships in enumerate(fleets, 1):
        if index == flen - 1:
            fleetstring += ships.name + ' and '
        elif index == flen:
            fleetstring += ships.name
        else:
            fleetstring += ships.name + ', '
    if flaginfo:
        fleetstring += " headed by the flagship %s" % flaginfo
    return fleetstring

def OOSfinalbattleresult(sector, world, target, worldlosses, targetlosses, freighters, worldfleets, targetfleets, 
    flag):
    #setting up strings and pluraliwahtever
    worldfleetstr = fleetnames(worldfleets, (flag['worldname'] if flag['world'] else False))
    wfstr = ('s' if len(worldfleets) > 1 else '')
    targetfleetstr = fleetnames(targetfleets, (flag['targetname'] if flag['target'] else False))
    tfstr = ('s' if len(targetfleets) > 1 else '')
    #stuff
    targetlink = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    worldlink = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    worldreport, targetreport = flagshipoutcome(flag['meet'], flag['worldloss'], True)
    #more fucking stuff
    dataatt = "Our %(atkfleets)s engaged %(target)s \
    %(deffleets)s in sector %(sector)s resulting in the enemy fleets \
    total obliteration!" % {'atkfleets': worldfleetstr,
    'deffleets': targetfleetstr, 'target': targetlink, 'sector': sector}

    #losses
    dataatt += " We <span class=\"red\">lost</span> "
    dataatt += losses(worldlosses) + " in the heat of battle."
    if freighters > 0:
        dataatt += " After the battle we seized %s freighters from %s that remained after the battle and \
        distributed them among our fleets" % (freighters, targetlink)

    datadef = "Our %(deffleets)s in %(sector)s was attacked by %(attacker)ss \
        %(atkfleets)s and the resulting battle ended in\
        total destruction of our fleet%(defplural)s :sadface:." % {'defplural': tfstr, 
        'atkfleets': worldfleetstr, 'deffleets': targetfleetstr, 'attacker': worldlink, 
        'sector': sector}
    datadef += ' But we managed to <span class="green">destroy</span> %s' % losses(worldlosses)

    return dataatt, datadef

def finalbattleresult(sector, world, target, loot, hangar, worldlosses, targetlosses, worldfleets, 
    targetfleets, flag):
    worldfleetstr = fleetnames(worldfleets, (flag['worldname'] if flag['world'] else False))
    wfstr = ('s' if len(worldfleets) > 1 else '')
    targetfleetstr = fleetnames(targetfleets, (flag['targetname'] if flag['target'] else False))
    tfstr = ('s' if len(targetfleets) > 1 else '')
    #stuff
    targetlink = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    worldlink = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    worldreport, targetreport = flagshipoutcome(flag['meet'], flag['worldloss'], True)
    table = tablelosses(targetlosses, worldlosses)
    loot = spoils(loot)
    
    dataatt = "Your %(worldfleet)s engaged %(targetfleet)s of world %(target)s! %(hl)s \
        Battle Report: %(hl)s </b> %(table)s %(flagreport)s %(hl)s After the battle, their puny fleet%(tplural)s cowers before yours and you \
        exact %(loot)s in reparations lest we utterly destroy their world." \
          % {'worldfleet':worldfleetstr, 'targetfleet':targetfleetstr, 'target':targetlink, 'table':table, 'loot':loot,
          'hl':hl, 'flagreport':worldreport, 'tplural': tfstr}

    datadef = "Your %(targetfleet)s was attacked by %(worldfleet)s of world %(enemy)s! %(hl)s \
        We <span class=\"red\">lost</span> %(defenselosses)s in the resulting conflict and managed to <span class=\"green\">destroy</span> \
        %(enemylosses)s in retaliation. %(flagreport)s %(hl)s We had to give them %(loot)s \
        in reparations in order to stop them from utterly destroying us after the battle! %(hl)s The war ends in a loss for us." \
          % {'worldfleet':worldfleetstr, 'targetfleet':targetfleetstr, 'enemy':worldlink, 
          'defenselosses':losses(targetlosses), 'enemylosses':losses(worldlosses), 'loot':loot, 
          'hl':hl, 'flagreport':targetreport}

    return dataatt, datadef


def warresult(region, world, target, actions, hanglosses, freighters, worldfleets, targetfleets):
    flagworld = checkflag(worldfleets)
    flagtarget = checkflag(targetfleets)
    worldfleetstr = fleetnames(worldfleets, (world.flagshipname if flagworld else False))
    targetfleetstr = fleetnames(targetfleets, (target.flagshipname if flagtarget else False))
    #stuff
    targetlink = '<a href="%s">%s</a>' % (target.get_absolute_url(), target.name)
    worldlink = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    hangarlosses = ' no ships at all'
    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from their orbital hangars,' % hangarlosses)
    loot = spoils(actions)
    dataatt = "Upon seeing your mighty %(atkfleets)s the %(deffleets)s of world %(enemy)s \
        surrenders. %(hl)s You exact %(loot)s in reparations lest you utterly \
        destroy their world." \
          % {'atkfleets': worldfleetstr, 'deffleets': targetfleetstr, 'hl': hl, 'loot': loot, 'enemy': targetlink}
 
    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from our orbital hangars,' % hangarlosses)

    datadef = "Your %(deffleets)s <span class=\"red\">surrenders</span> \
    at the sight of the mighty %(atkfleets)s of world %(enemy)s! %(hl)s\
     We had to give them %(loot)s \
    in reparations in order to stop them from utterly destroying us! %(hl)s The war ends in a humiliating loss for us." \
    % {'enemy': worldlink, 'loot': loot, 'hl':hl,
    'deffleets': targetfleetstr, 'atkfleets': worldfleetstr}

    return dataatt, datadef

def checkflag(fleets):
    for f in fleets:
        if f.flagship:
            return True
    return False

def spoils(spoilsdict):
    loot = []
    gdp = (spoilsdict['gdp']['amount'] if spoilsdict.has_key('gdp') else 0)
    growth = (spoilsdict['growth']['amount'] if spoilsdict.has_key('growth') else 0)
    budget = (spoilsdict['budget']['amount'] if spoilsdict.has_key('budget') else 0)
    fuel = (spoilsdict['warpfuel']['amount'] if spoilsdict.has_key('warpfuel') else 0)
    dur = (spoilsdict['duranium']['amount'] if spoilsdict.has_key('duranium') else 0)
    trit = (spoilsdict['tritanium']['amount'] if spoilsdict.has_key('tritanium') else 0)
    adam = (spoilsdict['adamantium']['amount'] if spoilsdict.has_key('adamantium') else 0)
    fre = (spoilsdict['freighters']['amount'] if spoilsdict.has_key('freighters') else 0)
    if gdp > 0:
        loot.append([ 'million GEU\'s worth of GDP',  gdp])
    if growth > 0:
        loot.append([ 'million GEU\'s worth of growth',  growth])
    if budget > 0:
        loot.append([ '%s in cash' % pl('GEU', budget),  budget])
    if fuel > 0:
        loot.append([ 'of warpfuel',  fuel])
    if dur > 0:
        loot.append([ 'of duranium',  dur])
    if trit > 0:
        loot.append([ 'of tritanium',  trit])
    if adam > 0:
        loot.append([ 'of adamantium',  adam])
    if fre > 0:
        loot.append([ '%s' % pl('freighter', fre),  fre])
    return utilities.resource_text(loot)

def rebelresult(outcome, deflosses):

    rebellosses = losses(deflosses)
    tot = sum(deflosses)

    conj = ('and' if tot == 0 else 'but')

    if 30 < outcome <= 100:
        data = "You found and battled the rebels! You managed to reduce their number, %(conj)s the fleet lost %(rebel)s in the conflict!"
    elif 5 < outcome <= 30:
        data = "Despite your thorough search of the entire system, you did not come upon any of the rebels."
    elif 1 <= outcome <= 5:
        data = "You found and entered into a fierce battle with the rebels, but they defeated the fleet in the engagement! %(hl)s We lost %(rebel)s \
               in the conflict and the rebels swell in number!"

    return data % {'rebel':rebellosses, 'conj':conj, 'hl':hl}


def raidresult(war, world, target, deflosses, attlosses, success, supersuccess, flost):

    worldfleet, targetfleet = fleetnames(war.region, world, target)
    data = "The small ships of your fleet %(worldfleet)s attempted a supply raid on fleet %(targetfleet)s of world \'%(targetname)s\'!<br>"

    if supersuccess:
        data += "Due to luck, superior training or some kind of divine favour, somehow their fleet did not spot us!<br>"
        if flost == 0:
            data += "Unfortunately we did not manage to destroy any freighters, so we returned to our fleet."
        else:
            data += "We quickly destroyed %(freighter)s freighters before their fleet was alerted, and hightailed it back to safety."

        return data % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.name, 'freighter':flost}

    else:
        targetlosses = losses(deflosses)
        worldlosses = losses(attlosses)
        data += "Their small ships spotted us. In the resulting conflict we destroyed%(targetlosses)s, and lost%(worldlosses)s.<br>"
        if success:
            if flost == 0:
                data += "We prevailed in the initial clash, but did not manage to destroy any freighters, so we returned to our fleet."
            else:
                data += "We prevailed in the initial clash, quickly destroyed %(freighter)s freighters before the rest of their fleet was alerted, \
                    and hightailed it back to safety."
        else:
            data += "Unfortunately their patrols held strong, and we did not manage to strike their supply lines.<br>\
                Our survivors limped back to the fleet."

        return data % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.name, \
            'targetlosses':targetlosses, 'worldlosses':worldlosses, 'freighter':flost}


def raidnotify(war, world, target, deflosses, attlosses, success, supersuccess, flost):

    ownfleet, enemyfleet = fleetnames(war.region, target, world)
    data = "Your fleet %(ownfleet)s was the target of a supply raid by fleet %(enemyfleet)s of world %(enemy)s!<br>"

    if supersuccess:
        data += "They completely eluded our patrols, "
        if flost == 0:
            data += "but did not manage to destroy any freighters, and quickly returned to their own fleet."
        else:
            data += "and destroyed %(freighter)s freighters before fleeing back to safety."

        return data % {'ownfleet':ownfleet, 'enemyfleet':enemyfleet, 'enemy':world.name, 'freighter':flost}

    else:
        defenselosses = losses(deflosses)
        enemylosses = losses(attlosses)
        data += "Our small ships confronted them, and in the resulting conflict we destroyed%(enemylosses)s, and lost%(defenselosses)s.<br>"
        if success:
            if flost == 0:
                data += "They beat our forces back, but could not destroy any freighters, so they returned to their fleet."
            else:
                data += "They beat our forces back and penetrated into our supply line, destroying %(freighter)s freighters before fleeing to safety."
        else:
            data += "We were steadfast in our defense and our attackers were forced to return fruitlessly back to their fleet."

    return data % {'ownfleet':ownfleet, 'enemyfleet':enemyfleet, 'enemy':world.name, 'enemylosses':enemylosses,
        'defenselosses':defenselosses, 'freighter':flost}


def peaceaccept(world):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)

    return "%s has accepted your peace offer and you are now at peace." % fullworld


def peacedecline(world):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)

    return "%s has rejected your peace offer! The war rages on." % fullworld


def peacerevoke(world):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)

    return "%s has changed their mind, and revoked the peace offer they sent you!" % fullworld


def salvagetext(dur, trit, adam):
    if dur + trit + adam == 0:
        return 'None'
    message = ''
    message += ('%s duranium' % dur if dur != 0 else '')
    message += (' and ' if dur != 0 and trit != 0 and adam == 0 else ', ' if dur != 0 else '')
    message += ('%s tritanium' % trit if trit != 0 else '')
    message += (' and ' if trit != 0 and adam != 0 else ', ' if trit != 0 else '')
    message += ('%s adamantium, ' % adam if adam != 0 else '')
    return message[:-2]


##########
### TRADES
##########

def tradeaccept(world, send, sendamount, receive, receiveamount):

    linkworld = reverse('stats_ind', args=(world.pk,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.name)

    return "%(fullworld)s has accepted your trade!<br>You send %(amountsend)s %(ressend)s, and their shipment of \
        %(amountrec)s %(sendrec)s is on the way." \
          % {'fullworld':fullworld, 'amountsend':sendamount, 'ressend':send, 'amountrec':receiveamount,'sendrec':receive}


def tradeacceptmoney(world, send, sendamount, receive, receiveamount):

    linkworld = reverse('stats_ind', args=(world.pk,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.name)

    return "%(fullworld)s has accepted your trade!<br>You send %(amountsend)s %(ressend)s, and receive %(amountrec)s %(sendrec)s." \
        % {'fullworld':fullworld,'amountsend':sendamount,'ressend':send,'amountrec':receiveamount,'sendrec':receive}


def directaidcompletion(world, resources):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    if len(resources) == 1:
        resource_text = "%s %s" % (resources[0][1], resources[0][0])
    else:
        action = {}
        for i, resource in enumerate(resources, 1):
            resource_text += "%s %s" % (resource[1], resource[0])
            if len(resources) - 1 == i:
                resource_text += ' and '
            else:
                resource_text += ', '
        resource_text = resource_text[:-2]
    return "We received %s from %s!" % (resource_text, fullworld)

def fleetaidcompletion(world, fleetname):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return "We recieved fleet %s from %s!" % (fleetname, fullworld)


def tradecompletion(world, resource, amount):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return "We received %(amount)s %(res)s from our trade with %(fullworld)s!" \
        % {'fullworld':fullworld,'amount':amount,'res':resource}

def tradecompletionships(world, ships):
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    count, ship = ships.split(' ')
    return "We received %(amount)s %(res)s from our trade with %(fullworld)s!" \
        % {'fullworld':fullworld,'amount':count,'res':ship}


def tradefail(resource):

    return "Your trade failed as you did not have enough %s!<br>You have been fined 20%% of your budget." % resource


def tradefailfreighters(resource):

    return "Your trade failed as you did not have enough freighters to transport your %s!<br>You have been fined 20%% of your budget." % resource


#########
### SPIES
#########

def spycaughtinfiltration(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s trying to sneak into your world!" % fullowner
    else:
        data += "trying to enter our world, but despite our best attempts we have no idea who his employers are."

    return data


def spycaughtpropaganda(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s attempting to spread discontent among the people!" % fullowner
    else:
        data += "trying to incite hatred for your rule among the people, but you could not find out who sent him."

    return data


def spycaughtgunrun(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s attempting to smuggle tech to the rebels in your system!" % fullowner
    else:
        data += "from an unknown employer smuggling tech to some rebels."

    return data


def spycaughtintel(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s setting up an electronic surveillance network on your world!" % fullowner
    else:
        data += "setting up a surveillance network, but you could not discover his employers."

    return data


def spycaughtsab(spy, reveal, installtype):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if installtype == 'yard':
        installname = 'shipyards'
    elif installtype == 'fuel':
        installname = 'warpfuel refineries'
    elif installtype == 'dur':
        installname = 'duranium mines'
    elif installtype == 'trit':
        installname = 'tritanium mines'
    elif installtype == 'adam':
        installname = 'adamantium mines'

    if reveal:
        data += "from %s in his attempt to destroy one of our %s!" % (fullowner, installname)
    else:
        data += "and his team trying to destroy one of our %s, but you could not discover his employers." % installname

    return data


def spycaughtsabhangars(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.pk,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data = "from %s in his attempt to sabotage our orbital hangars!" % fullowner
    else:
        data = "and his team trying to sabotage our orbital hangars, but you could not discover his employers."

    return data


def counterintkilled(spy, world):
    linkworld = reverse('stats_ind', args=(world.pk,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.name)

    return "Your spy \'%s\' was caught in a counterintelligence sweep on the world of %s and killed!" % (spy.name, fullworld)


def notifysab(installtype):

    if installtype == 'yard':
        installtype = 'shipyards'
    elif installtype == 'fuel':
        installtype = 'warpfuel refineries'
    elif installtype == 'dur':
        installtype = 'duranium mines'
    elif installtype == 'trit':
        installtype = 'tritanium mines'
    elif installtype == 'adam':
        installtype = 'adamantium mines'

    return "One of your %s has been critically damaged in a covert attack!<br>We should make a counterintelligence search at once!" % installtype


def notifysabhangars(deflosses):

    hangarlosses = losses(deflosses)

    return "Our orbital hangars have been damaged in a covert attack!<br>We lost%s in the attempt, \
        and should make a counterintelligence search at once!" % hangarlosses


def notifyspyintercept(target, sender, resname, resamount):

    linktarget = reverse('stats_ind', args=(target.pk,))
    fulltarget = '<a href="%s">%s</a>' % (linktarget, target.name)
    linksender = reverse('stats_ind', args=(sender.pk,))
    fullsender = '<a href="%s">%s</a>' % (linksender, sender.name)

    return "Your spy's intel network on %s has intercepted communications showing that it just received %s %s from the world of %s!" \
        % (fulltarget, resamount, resname, fullsender)


def notifyspyinterceptsend(sender, target, resname, resamount):

    linksender = reverse('stats_ind', args=(sender.pk,))
    fullsender = '<a href="%s">%s</a>' % (linksender, sender.name)
    linktarget = reverse('stats_ind', args=(target.pk,))
    fulltarget = '<a href="%s">%s</a>' % (linktarget, target.name)

    return "Your spy's intel network on %s has intercepted communications showing that it just sent %s %s to the world of %s!" \
        % (fullsender, resamount, resname, fulltarget)


#############
### SHIP WARP
#############

def notenough(amount, shiptext, regionfrom, regionto, key):

    return "Your attempt to warp %s %s from %s to %s failed as you did not have enough %s." \
         % (amount, shiptext, regionfrom, regionto, key)


def mothball(amount, shiptext, key, direction):

    data = "You failed to "

    if direction == 'plus':
        data += "reactivate %s %s from your hangars as you did not have enough %s." % (amount, shiptext, key)
    elif direction == 'minus':
        data += "mothball %s %s as you did not have enough %s." % (amount, shiptext, key)

    return data

def recalled(fleetname, world):
    fulldick = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)
    return "%s has recalled their fleet %s!" % (fulldick, fleetname)

#def sendback()


###############
### ACTION NEWS
###############

def offerpeace(world, target): #type 1
    fullworld = '<a href="%s">%s</a>' % (world.get_absolute_url(), world.name)

    data = "You have been offered a white peace by %s. &nbsp;&nbsp; \
            <input type='submit' name='acceptpeace' value='Accept' class='button'/> &nbsp;\
            <input type='submit' name='declinepeace' value='Decline' class='redbutton'/>" % fullworld

    return data


def newbevent(name): #type 2
    imgloc = static('actionnews/newworld.gif')
    data = """<center> \
            Welcome to the Galaxy, %s! Choose the path your world has taken carefully. \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="newworld"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='noobmoney' value='Economy' class='button'  \
                    title='You have 600 GEU for you to spend however you see fit.'/></td>  \
            <td class='center'><input type='submit' name='noobqol' value='Welfare' class='button'  \
                    title='Your people love you and have higher quality of life.'/></td>  \
            <td class='center'><input type='submit' name='noobsecurity' value='Security' class='button'  \
                    title='Your rule is extremely solid.'/></td>  \
            <td class='center'><input type='submit' name='noobmilitary' value='Military' class='button'  \
                    title='You have a strong military.'/></td>  \
            </tr> \
            </table> \
            </center>""" % (name, imgloc)
    return data


def fleetevent(): #type 3
    imgloc = static('actionnews/fleet.gif')
    data = """<center> \
            The admirals have convened to discuss the direction of the fleet. <br> What will you decide to focus effort on? \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="fleet"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='fleetresearch' value='Research' class='button'  \
                    title='You will gain research towards the next ship tier.'/></td>  \
            <td class='center'><input type='submit' name='fleetshipyard' value='Construction' class='button'  \
                    title='You will gain a new shipyard.'/></td>  \
            <td class='center'><input type='submit' name='fleettraining' value='Training' class='button'  \
                    title='You will gain training for your home fleet.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def asteroidevent(): #type 4
    imgloc = static('actionnews/asteroidmine.gif')
    data = """<center> \
            You track an asteroid entering your system to find it is saturated with resources. <br> \
            However, due to its small size you may only build one mine on it. What do you choose? \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="asteroidmine"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='asteroidduranium' value='Duranium' class='button'  \
                    title='You will gain one duranium mine.'/></td>  \
            <td class='center'><input type='submit' name='asteroidtritanium' value='Tritanium' class='button'  \
                    title='You will gain one tritanium mine.'/></td>  \
            <td class='center'><input type='submit' name='asteroidadamantium' value='Adamantium' class='button'  \
                    title='You will gain one adamantium mine.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def dangerasteroid(): #type 5
    imgloc = static('actionnews/dangerasteroid.gif')
    data = """<center> \
            Your fleet intelligence detects an asteroid on a collision course <br> \
            directly for the planet! What should be done? \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="dangerasteroid"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='dasteroiddeflect' value='Deflect' class='button'  \
                    title='Get your support ships to deflect it harmlessly into space, at the cost of 50 warpfuel.'/></td>  \
            <td class='center'><input type='submit' name='dasteroidsubcontract' value='Subcontract' class='button'  \
                    title='Pay a civilian company to deflect it for you, at the cost of 500 GEU.'/></td>  \
            <td class='center'><input type='submit' name='dasteroidredirect' value='Redirect' class='button'  \
                    title='Redirect it onto a rebel area on your planet at the cost of 20 warpfuel. \
                    Rebels will be heavily reduced but you will lose perception.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def rebeladmiral(): #type 6
    imgloc = static('actionnews/rebeladmiral.gif')
    data = """<center> \
            One of your admirals is gathering popularity with the people. You have even <br> \
            heard rumours that he might dare to rise against you! What should be done?\
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="rebeladmiral"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='radmiralignore' value='Ignore' class='button'  \
                    title='Your people love you, they would never rebel. Ignore this annoyance.'/></td>  \
            <td class='center'><input type='submit' name='radmiralbribe' value='Bribe' class='button'  \
                    title='Pay 250 GEU to convince the admiral to retire with a comfortable pension.'/></td>  \
            <td class='center'><input type='submit' name='radmiralspy' value='Assassinate' class='button'  \
                    title='Send a spy to cause the admiral to have an \'unfortunate accident\'.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def traderaiders(): #type 7
    imgloc = static('actionnews/traderaiders.gif')
    data = """<center> \
            Raiders have been harassing your trade ships. What should be done? \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="traderaiders"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='traidersattack' value='Attack' class='button'  \
                    title='This cannot stand! Send your home fleet to crush these rats.'/></td>  \
            <td class='center'><input type='submit' name='traidersbribe' value='Bribe' class='button'  \
                    title='Pay 500 GEU to try and make them go away.'/></td>  \
            <td class='center'><input type='submit' name='traidersignore' value='Ignore' class='button'  \
                    title='We have far more important things to worry about than a couple of petty raiders.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def durasteroid(): #type 8
    imgloc = static('actionnews/durasteroid.gif')
    data = """<center> \
            An asteroid impacts on your world, with minor casualties. Quality of <br> \
            life drops slightly, but you discover the asteroid is full of duranium! \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="durasteroid"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='durasteroidmine' value='Mine' class='button'  \
                    title='Extract as much as you can.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def fuelexplode(): #type 9
    imgloc = static('actionnews/fuelexplode.gif')
    data = """<center> \
            One of your fuel refineries suffers a catastrophic failure and explodes! \
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="fuelexplode"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='fuelexplodeaccept' value='Accept' class='button'  \
                    title='Dayum shame.'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data


def xenu(): #type 10
    imgloc = static('actionnews/xenu.gif')
    data = """<center> \
            A galactic despot arrives in orbit in what looks like a DC-8 airplane from <br>\
            old Earth. He asks if he can dump off some spare spirits on your world.
            <p class="halfline">&nbsp;</p> \
            <img src="%s" alt="xenu"> \
            <p class="halfline">&nbsp;</p> \
            <table> \
            <tr> \
            <td class='center'><input type='submit' name='xenuaccept' value='Accept' class='button'  \
                    title='Yeah, why not? Could be a laff.'/></td>  \
            <td class='center'><input type='submit' name='xenurefuse' value='Refuse' class='button'  \
                    title='lol r u crazy m8 gtfo b4 u get hooked in da gabber'/></td>  \
            </tr> \
            </table> \
            </center>""" % imgloc
    return data
