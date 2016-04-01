# Django Imports
from django.core.urlresolvers import reverse
from django.templatetags.static import static

# WaW Imports
import wawmembers.variables as v
from wawmembers.utilities import plural as pl

'''
HTML generation for news items.
'''


hl = '<p class="halfline">&nbsp;</p>'

##############
### RUMSODDIUM
##############

def rumsoddium(world):
    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%s seized your prized rumsoddium after defeating you in your war!" % fullworld


def rumsodmilitaryreceive(world):
    linkworld = reverse('stats_ind', args=(world.worldid,))
    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

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
    linkinviter = reverse('stats_ind', args=(inviter.worldid,))

    fullalliance = '<a href="%s">%s</a>' % (linkalliance, alliance.alliance_name)
    fullinviter = '<a href="%s">%s</a>' % (linkinviter, inviter.world_name)

    status = ('leader' if inviter.leader else 'officer')

    return "You have been invited to the federation %(alliance)s by their %(status)s, %(inviter)s! Go to their federation page to accept." \
        % {'alliance':fullalliance, 'status':status, 'inviter':fullinviter}


def withdrawalmade(officer, amount):
    linkofficer = reverse('stats_ind', args=(officer.worldid,))

    fullofficer = '<a href="%s">%s</a>' % (linkofficer, officer.world_name)

    return "%(amount)s GEUs have been withdrawn from your federation bank by your officer %(officer)s." \
        % {'amount':amount, 'officer':fullofficer}


def depositmade(member, amount):
    linkmember = reverse('stats_ind', args=(member.worldid,))

    fullmember = '<a href="%s">%s</a>' % (linkmember, member.world_name)

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
    linkofficer = reverse('stats_ind', args=(officer.worldid,))

    fullofficer = '<a href="%s">%s</a>' % (linkofficer, officer.world_name)

    return "Your officer %s has resigned in your alliance!" % fullofficer


def successor(leader):
    linkleader = reverse('stats_ind', args=(leader.worldid,))

    fullleader = '<a href="%s">%s</a>' % (linkleader, leader.world_name)

    return "%s, the leader of your alliance, has resigned and given you command!" % fullleader


#######
### WAR
#######

def wardec(world,reason):
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%s has declared war on you! They gave the following reason: <i>%s</i>." % (fullworld,reason)


def fleetnames(region, world, target):
    if region == 'A':
        worldfleet = world.fleetname_inA
        targetfleet = target.fleetname_inA
    elif region == 'B':
        worldfleet = world.fleetname_inB
        targetfleet = target.fleetname_inB
    elif region == 'C':
        worldfleet = world.fleetname_inC
        targetfleet = target.fleetname_inC
    elif region == 'D':
        worldfleet = world.fleetname_inD
        targetfleet = target.fleetname_inD
    return worldfleet, targetfleet


def losses(shiplist):
    sh1, sh2, sh3, sh4, sh5, sh6, sh7, sh8, sh9 = shiplist
    fighters = ' %s %s,' % (sh1, pl('fighter', sh1))
    corvettes = ' %s %s,' % (sh2, pl('corvette', sh2))
    lcruisers = ' %s %s,' % (sh3, pl('light cruiser', sh3))
    destroyers = ' %s %s,' % (sh4, pl('destroyer', sh4))
    frigates = ' %s %s,' % (sh5, pl('frigate', sh5))
    hcruisers = ' %s %s,' % (sh6, pl('heavy cruiser', sh6))
    bcruisers = ' %s %s,' % (sh7, pl('battlecruiser', sh7))
    battleships = ' %s %s,' % (sh8, pl('battleship', sh8))
    dreadnoughts = ' %s %s,' % (sh9, pl('dreadnought', sh9))

    if sh9 == 0:
        loss = fighters + corvettes + lcruisers + destroyers + frigates + hcruisers + bcruisers + ' and' + battleships[:-1]
        if sh8 == 0:
            loss = fighters + corvettes + lcruisers + destroyers + frigates + hcruisers + ' and' + bcruisers[:-1]
            if sh7 == 0:
                loss = fighters + corvettes + lcruisers + destroyers + frigates + ' and' + hcruisers[:-1]
                if sh6 == 0:
                    loss = fighters + corvettes + lcruisers + destroyers + ' and' + frigates[:-1]
                    if sh5 == 0:
                        loss = fighters + corvettes + lcruisers + ' and' + destroyers[:-1]
                        if sh4 == 0:
                            loss = fighters + corvettes + ' and' + lcruisers[:-1]
                            if sh3 == 0:
                                loss = fighters + ' and' + corvettes[:-1]
                                if sh2 == 0:
                                    loss = fighters[:-1]
                                    if sh1 == 0:
                                        loss = ' no ships at all'
    else:
        loss = fighters + corvettes + lcruisers + destroyers + frigates + hcruisers + bcruisers + battleships + \
            ' and' + dreadnoughts[:-1]

    return loss


def tablelosses(targetlosses, worldlosses):
    index = 1
    table = '<table width="60%" class="striped supplydisplay"><tr class="verydark"><b><td class="hidden nohl"></td>\
        <td class="green center">We destroyed</td><td class="red center">We lost</td></b></tr>'

    for i in range(9):
        if not targetlosses[-1-i] == worldlosses[-1-i] == 0:
            index = 9-i
            break

    for i in range(index):
        table += '<tr class="%s"><td class="leftpad">%s</td><td class="center">%s</td><td class="center">%s</td></tr>' \
          % (('light' if not i % 2 else 'dark'), v.shipindices[i], targetlosses[i], worldlosses[i])

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


def battleresult(region, world, target, deflosses, attlosses, flost, flagworld, flagtarget, flagmeet, flagworldlose, flagtargetlose):

    worldfleet, targetfleet = fleetnames(region, world, target)
    worldflag = (', headed by the flagship <i>%s</i>,<br>' % world.flagshipname if flagworld else '')
    targetflag = (', headed by the flagship <i>%s</i>,' % target.flagshipname if flagtarget else '')
    worldreport, targetreport = flagshipoutcome(flagmeet, flagworldlose, flagtargetlose)

    table = tablelosses(deflosses, attlosses)
    freighter = ('' if flost == 0 else '%s You also managed to destroy %s %s in the heat of battle.' % (hl, flost, pl('freighter', flost)))

    dataatt = "<b>Your fleet <i>%(worldfleet)s</i>%(worldflag)s engaged fleet <i>%(targetfleet)s</i>%(targetflag)s of world %(targetname)s! \
        %(hl)s Battle Report: %(hl)s </b> %(table)s %(flagreport)s %(freighter)s" \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, 'table':table, 'freighter':freighter, 'hl':hl,
          'worldflag':worldflag, 'targetflag':targetflag, 'flagreport':worldreport}

    defenselosses = losses(deflosses)
    enemylosses = losses(attlosses)
    linkenemy = reverse('stats_ind', args=(world.worldid,))
    fullenemy = '<a href="%s">%s</a>' % (linkenemy, world.world_name)
    pluralise = ('was' if flost == 1 else 'were')
    freighterdef = ('' if flost == 0 else '%s %s of your freighters %s also destroyed in the heat of battle.' % (hl, flost, pluralise))

    conj = 'and <span class="green">destroyed</span>'
    if enemylosses == ' no ships at all' and defenselosses == ' no ships at all':
        mod = desc = ''
    elif enemylosses == ' no ships at all':
        mod = ''
        desc = 'crushingly '
    elif defenselosses == ' no ships at all':
        mod = 'mighty'
        desc = 'pathetically '
    else:
        mod = desc = ''
        conj = 'but we managed to <span class="green">destroy</span>'

    datadef = "Your %(mod)s fleet <i>%(targetfleet)s</i>%(targetflag)s was %(desc)sattacked by fleet <i>%(worldfleet)s</i>%(worldflag)s \
        of world %(enemy)s! %(hl)s We <span class=\"red\">lost</span> %(defenselosses)s in the resulting conflict, %(conj)s %(enemylosses)s \
        in retaliation! %(flagreport)s %(freighter)s" \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, 'hl':hl, 'mod':mod, 'desc':desc, \
          'enemy':fullenemy, 'defenselosses':defenselosses, 'enemylosses':enemylosses, 'conj':conj, 'freighter':freighterdef, \
          'worldflag':worldflag, 'targetflag':targetflag, 'flagreport':targetreport}

    return dataatt, datadef


def finalbattleresult(region, world, target, deflosses, attlosses, gdp, growth, budget, fuel, dur, trit, adam, hanglosses, flost, freighters,
  flagworld, flagtarget, flagmeet, flagworldlose, flagtargetlose):

    worldfleet, targetfleet = fleetnames(region, world, target)
    worldflag = (', headed by the flagship <i>%s</i>,<br>' % world.flagshipname if flagworld else '')
    targetflag = (', headed by the flagship <i>%s</i>,' % target.flagshipname if flagtarget else '')
    worldreport, targetreport = flagshipoutcome(flagmeet, flagworldlose, flagtargetlose)
    hangarlosses = losses(hanglosses)
    loot = spoils(growth, budget, fuel, dur, trit, adam, freighters)

    table = tablelosses(deflosses, attlosses)
    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from their orbital hangars,' % hangarlosses)
    freighter = ('' if flost == 0 else '%s You also managed to destroy %s %s in the heat of battle.' % (hl, flost, pl('freighter', flost)))

    dataatt = "Your fleet <i>%(worldfleet)s</i>%(worldflag)s engaged fleet <i>%(targetfleet)s</i>%(targetflag)s of world %(targetname)s! %(hl)s \
        Battle Report: %(hl)s </b> %(table)s %(flagreport)s %(freighter)s %(hl)s After the battle, their puny fleet cowers before yours and you \
        exact %(gdp)s million GEUs worth of GDP,%(hangar)s%(loot)s in reparations lest you utterly destroy their world." \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, 'table':table, 'gdp':gdp, 'loot':loot,
          'hangar':toaddhangar, 'freighter':freighter, 'hl':hl, 'worldflag':worldflag, 'targetflag':targetflag, 'flagreport':worldreport}

    defenselosses = losses(deflosses)
    enemylosses = losses(attlosses)
    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from our orbital hangars,' % hangarlosses)
    pluralise = ('was' if flost == 1 else 'were')
    freighter = ('' if flost == 0 else '%s %s of your freighters %s also destroyed in the heat of battle.' % (hl, flost, pluralise))
    linkenemy = reverse('stats_ind', args=(world.worldid,))
    fullenemy = '<a href="%s">%s</a>' % (linkenemy, world.world_name)

    datadef = "Your fleet <i>%(targetfleet)s</i>%(targetflag)s was attacked by fleet <i>%(worldfleet)s</i>%(worldflag)s of world %(enemy)s! %(hl)s \
        We <span class=\"red\">lost</span> %(defenselosses)s in the resulting conflict and managed to <span class=\"green\">destroy</span> \
        %(enemylosses)s in retaliation. %(flagreport)s %(freighter)s %(hl)s We had to give them %(gdp)s million GEUs worth of GDP,%(hangar)s%(loot)s \
        in reparations in order to stop them from utterly destroying us after the battle! %(hl)s The war ends in a loss for us." \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'enemy':fullenemy, 'defenselosses':defenselosses, 'enemylosses':enemylosses,
          'gdp':gdp, 'loot':loot, 'hangar':toaddhangar, 'freighter':freighter, 'hl':hl, 'worldflag':worldflag, 'targetflag':targetflag,
          'flagreport':targetreport}

    return dataatt, datadef


def warresult(region, world, target, gdp, growth, budget, fuel, dur, trit, adam, hanglosses, freighters, flagworld, flagtarget):

    worldfleet, targetfleet = fleetnames(region, world, target)
    loot = spoils(growth, budget, fuel, dur, trit, adam, freighters)
    worldflag = (', headed by the flagship <i>%s</i>,<br>' % world.flagshipname if flagworld else '')
    targetflag = (', headed by the flagship <i>%s</i>,' % target.flagshipname if flagtarget else '')
    hangarlosses = losses(hanglosses)
    loot = spoils(growth, budget, fuel, dur, trit, adam, freighters)

    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from their orbital hangars,' % hangarlosses)

    dataatt = "Upon seeing your mighty fleet <i>%(worldfleet)s</i>%(worldflag)s the fleet <i>%(targetfleet)s</i>%(targetflag)s of world \
        %(targetname)s surrenders. %(hl)s You exact %(gdp)s million GEUs worth of GDP,%(hangar)s%(loot)s in reparations lest you utterly \
        destroy their world." \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, 'gdp':gdp, 'loot':loot, 'hangar':toaddhangar,
          'hl':hl, 'worldflag':worldflag, 'targetflag':targetflag}

    linkenemy = reverse('stats_ind', args=(world.worldid,))
    fullenemy = '<a href="%s">%s</a>' % (linkenemy, world.world_name)
    toaddhangar = ('' if hangarlosses == ' no ships at all' else ' %s from our orbital hangars,' % hangarlosses)

    datadef = "Your fleet <i>%(targetfleet)s</i>%(targetflag)s <span class=\"red\">surrenders</span> at the sight of the mighty fleet \
        <i>%(worldfleet)s</i>%(worldflag)s of world %(enemy)s! %(hl)s We had to give them %(gdp)s million GEUs worth of GDP,%(hangar)s%(loot)s \
        in reparations in order to stop them from utterly destroying us! %(hl)s The war ends in a humiliating loss for us." \
          % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'enemy':fullenemy,'gdp':gdp, 'loot':loot, 'hangar':toaddhangar, 'hl':hl,
          'worldflag':worldflag, 'targetflag':targetflag}

    return dataatt, datadef


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


def spoils(growth, budget, fuel, dur, trit, adam, fre):

    growth = ('' if growth == 0 else ' %s million GEU\'s worth of growth,' % growth)
    budget = ('' if budget == 0 else ' %s %s in cash,' % (budget, pl('GEU', budget)))
    fuel = ('' if fuel == 0 else ' %s %s of warpfuel,' % (fuel, pl('canister', fuel)))
    dur = ('' if dur == 0 else ' %s %s of duranium,' % (dur, pl('ton', dur)))
    trit = ('' if trit == 0 else ' %s %s of tritanium,' % (trit, pl('ton', trit)))
    adam = ('' if adam == 0 else ' %s %s of adamantium,' % (adam, pl('ton', adam)))
    fre = ('' if fre == 0 else ' %s %s,' % (fre, pl('freighter', fre)))

    if fre == '':
        spoils = growth + budget + fuel + dur + trit + ' and' + adam[:-1]
        if adam == '':
            spoils = growth + budget + fuel + dur + ' and' + trit[:-1]
            if trit == '':
                spoils = growth + budget + fuel + ' and' + dur[:-1]
                if dur == '':
                    spoils = growth + budget + ' and' + fuel[:-1]
                    if fuel == '':
                        spoils = growth + ' and' + budget[:-1]
                        if budget == '':
                            spoils = growth[:-1]
                            if growth == '':
                                spoils = ""
    else:
        spoils = growth + budget + fuel + dur + trit + adam + ' and' + fre[:-1]

    return spoils


def raidresult(war, world, target, deflosses, attlosses, success, supersuccess, flost):

    worldfleet, targetfleet = fleetnames(war.region, world, target)
    data = "The small ships of your fleet %(worldfleet)s attempted a supply raid on fleet %(targetfleet)s of world \'%(targetname)s\'!<br>"

    if supersuccess:
        data += "Due to luck, superior training or some kind of divine favour, somehow their fleet did not spot us!<br>"
        if flost == 0:
            data += "Unfortunately we did not manage to destroy any freighters, so we returned to our fleet."
        else:
            data += "We quickly destroyed %(freighter)s freighters before their fleet was alerted, and hightailed it back to safety."

        return data % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, 'freighter':flost}

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

        return data % {'worldfleet':worldfleet, 'targetfleet':targetfleet, 'targetname':target.world_name, \
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

        return data % {'ownfleet':ownfleet, 'enemyfleet':enemyfleet, 'enemy':world.world_name, 'freighter':flost}

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

    return data % {'ownfleet':ownfleet, 'enemyfleet':enemyfleet, 'enemy':world.world_name, 'enemylosses':enemylosses,
        'defenselosses':defenselosses, 'freighter':flost}


def peaceaccept(world):
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%s has accepted your peace offer and you are now at peace." % fullworld


def peacedecline(world):
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%s has rejected your peace offer! The war rages on." % fullworld


def peacerevoke(world):
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

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

    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%(fullworld)s has accepted your trade!<br>You send %(amountsend)s %(ressend)s, and their shipment of \
        %(amountrec)s %(sendrec)s is on the way." \
          % {'fullworld':fullworld, 'amountsend':sendamount, 'ressend':send, 'amountrec':receiveamount,'sendrec':receive}


def tradeacceptmoney(world, send, sendamount, receive, receiveamount):

    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "%(fullworld)s has accepted your trade!<br>You send %(amountsend)s %(ressend)s, and receive %(amountrec)s %(sendrec)s." \
        % {'fullworld':fullworld,'amountsend':sendamount,'ressend':send,'amountrec':receiveamount,'sendrec':receive}


def directaidcompletion(world, send, sendamount):

    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "We received %(amountsend)s %(ressend)s from %(fullworld)s!" \
        % {'fullworld':fullworld,'amountsend':sendamount,'ressend':send}


def tradecompletion(world, send, sendamount):

    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

    return "We received %(amountsend)s %(ressend)s from our trade with %(fullworld)s!" \
        % {'fullworld':fullworld,'amountsend':sendamount,'ressend':send}


def tradefail(resource):

    return "Your trade failed as you did not have enough %s!<br>You have been fined 20%% of your budget." % resource


def tradefailfreighters(resource):

    return "Your trade failed as you did not have enough freighters to transport your %s!<br>You have been fined 20%% of your budget." % resource


#########
### SPIES
#########

def spycaughtinfiltration(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s trying to sneak into your world!" % fullowner
    else:
        data += "trying to enter our world, but despite our best attempts we have no idea who his employers are."

    return data


def spycaughtpropaganda(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s attempting to spread discontent among the people!" % fullowner
    else:
        data += "trying to incite hatred for your rule among the people, but you could not find out who sent him."

    return data


def spycaughtgunrun(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s attempting to smuggle tech to the rebels in your system!" % fullowner
    else:
        data += "from an unknown employer smuggling tech to some rebels."

    return data


def spycaughtintel(spy, reveal):
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data += "from %s setting up an electronic surveillance network on your world!" % fullowner
    else:
        data += "setting up a surveillance network, but you could not discover his employers."

    return data


def spycaughtsab(spy, reveal, installtype):
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
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
    linkowner = reverse('stats_ind', args=(spy.owner.worldid,))

    fullowner = '<a href="%s">%s</a>' % (linkowner, spy.owner.world_name)
    data = "You caught a spy called \'%s\' " % spy.name

    if reveal:
        data = "from %s in his attempt to sabotage our orbital hangars!" % fullowner
    else:
        data = "and his team trying to sabotage our orbital hangars, but you could not discover his employers."

    return data


def counterintkilled(spy, world):
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

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

    linktarget = reverse('stats_ind', args=(target.worldid,))
    fulltarget = '<a href="%s">%s</a>' % (linktarget, target.world_name)
    linksender = reverse('stats_ind', args=(sender.worldid,))
    fullsender = '<a href="%s">%s</a>' % (linksender, sender.world_name)

    return "Your spy's intel network on %s has intercepted communications showing that it just received %s %s from the world of %s!" \
        % (fulltarget, resamount, resname, fullsender)


def notifyspyinterceptsend(sender, target, resname, resamount):

    linksender = reverse('stats_ind', args=(sender.worldid,))
    fullsender = '<a href="%s">%s</a>' % (linksender, sender.world_name)
    linktarget = reverse('stats_ind', args=(target.worldid,))
    fulltarget = '<a href="%s">%s</a>' % (linktarget, target.world_name)

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


###############
### ACTION NEWS
###############

def offerpeace(world, target): #type 1
    linkworld = reverse('stats_ind', args=(world.worldid,))

    fullworld = '<a href="%s">%s</a>' % (linkworld, world.world_name)

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
