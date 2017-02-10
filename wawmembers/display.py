import wawmembers.variables as v

'''
Converts numbers to text descriptions.
'''

def training_display(cur, maxt):
    try:
        ratio = float(cur)/float(maxt)
    except:
        ratio = 0
    if 0 <= ratio < 0.2:
        return 'Ragtag'
    elif 0.2 <= ratio < 0.4:
        return 'Disorganised'
    elif 0.4 <= ratio < 0.6:
        return 'Coordinated'
    elif 0.6 <= ratio < 0.8:
        return 'Well-trained'
    elif ratio >= 0.8:
        return 'Finely-honed'

def personalshipname(shiptype):
    if shiptype == 1:
        name = 'personal fighter'
    elif shiptype == 2:
        name = 'militarised yacht'
    elif shiptype == 3:
        name = 'command ship'
    else:
        name = None
    return name

def weariness_display(weariness):
    if weariness == 200:
        return 'Raring to go'
    elif 160 <= weariness < 200:
        return 'Fresh'
    elif 120 <= weariness < 160:
        return 'Ready'
    elif 80 <= weariness < 120:
        return 'Tired'
    elif 40 <= weariness < 80:
        return 'Weary'
    elif weariness < 40:
        return 'Exhausted'

def fleet_display(milinfo, sectorlist, main=True):
    output = []
    #determine highest tier ship to display
    highest = 0
    for sector in sectorlist:
        for ship in list(milinfo[sector]['totalships']._meta.fields)[v.fleetindex:]:
            if milinfo[sector]['totalships'].__dict__[ship.name] > 0:
                shipindex = list(milinfo[sector]['totalships']._meta.fields)[v.fleetindex:].index(ship)
                if shipindex > highest:
                    highest = shipindex
    #order is sector, training, weariness, base power, fuel cost and ships
    output.append(sectorlist)
    traininglist = ['<b>Training</b>']
    wearinesslist = ['<b>Weariness</b>']
    fleetslist = ['<b>Fleets in Sector</b>']
    powerlist = ['<b>Base Power</b>']
    fuellist = ['<b>Base Fuel Cost</b>']
    for sector in sectorlist:
        if milinfo[sector]['fleets'] is 0: #no ships present in sector
            traininglist.append('-')
            wearinesslist.append('-')
            fleetslist.append('-')
            powerlist.append('-')
            fuellist.append('-')
        else:
            traininglist.append(training_display(milinfo[sector]['current'], milinfo[sector]['max']))
            wearinesslist.append(weariness_display(milinfo[sector]['weariness'] / milinfo[sector]['fleets']))
            fleetslist.append(milinfo[sector]['fleets'])
            powerlist.append(milinfo[sector]['power'])
            fuellist.append(milinfo[sector]['fuelcost'])
    output.append(traininglist)
    output.append(wearinesslist)
    if main:
        output.append(fleetslist)
    output.append(powerlist)
    output.append(fuellist)
    shiplist = list(milinfo[sectorlist[0]]['totalships']._meta.fields)[v.fleetindex:]
    for sector in sectorlist: #sets sectors with 0 fleets to display a - instead of 0
        if milinfo[sector]['fleets'] is 0:
            for ship in shiplist:
                milinfo[sector]['totalships'].__dict__[ship.name] = '-'
    if main:
        for i in range (highest+1): #iterates through the tiers and appends the data as a list
            output.append([shiplist[i].name.replace('_', ' '),
                milinfo[sectorlist[0]]['totalships'].__dict__[shiplist[i].name], 
                milinfo[sectorlist[1]]['totalships'].__dict__[shiplist[i].name],
                milinfo[sectorlist[2]]['totalships'].__dict__[shiplist[i].name],
                milinfo[sectorlist[3]]['totalships'].__dict__[shiplist[i].name],
                milinfo[sectorlist[4]]['totalships'].__dict__[shiplist[i].name]])
    else:
        for i in range (highest+1): #could probably be done in a more elegant way, but #notime
            output.append([shiplist[i].name.replace('_', ' '),
                milinfo[sectorlist[0]]['totalships'].__dict__[shiplist[i].name], 
                milinfo[sectorlist[1]]['totalships'].__dict__[shiplist[i].name],
                milinfo[sectorlist[2]]['totalships'].__dict__[shiplist[i].name],
                milinfo[sectorlist[3]]['totalships'].__dict__[shiplist[i].name],])
    return output

#formats build information and amount for easy html rendering
def milpolicydisplay(world):
    costs = v.shipcosts(world.sector)
    iterlist = ['freighters']
    for element in v.tiers:
        iterlist.append(element.replace(' ', '_').lower() + 's')
        if element == world.techlevel:
            break #max tech level we can produce

    #now assemble a list of dictionaries, not a list of lists
    #because heidi didn't just <td></td><td></td>
    #he absolutely had to add spans and shit
    displaylist = []
    for element in iterlist:
        #human friendly name
        appendage = {
            'name': element.replace('_', ' ').capitalize()[:len(element) - 1],
            'fname': element}
        appendage.update(costs[element])
        displaylist.append(appendage) 
    return displaylist



#takes the queryset and prepares for easy display
def fleetmanagementdisplay(fleetlist, owner):
    renderlist = []
    for fleet in fleetlist:
        tmprender = []
        highest = highestship(fleet)
        if fleet.world == fleet.controller:
            tmprender.append(['Status', 'Owned'])
        elif fleet.world == owner:
            tmprender.append(['Status', fleet.controller])
        else:
            tmprender.append(['Status', fleet.world])
        tmprender.append(['Sector', fleet.sector.capitalize()])
        tmprender.append(['Training', training_display(fleet.training, fleet.maxtraining())])
        tmprender.append(['Weariness', weariness_display(fleet.weariness)])
        tmprender.append(['Base power', fleet.power()])
        tmprender.append(['Fuelcost', fleet.fuelcost()])
        for ship in v.shipindices:
            r1 = ship.replace('_', ' ').capitalize()
            r2 = fleet.__dict__[ship]
            tmprender.append([r1, r2])
            if ship == highest:
                break
        renderdict = {'name': fleet.name, 'fleetdata': tmprender, 'pk': fleet.pk}
        renderlist.append(renderdict)
    return renderlist

def fleetexchangedisplay(f, highest): #f stand sfor fleet
    renderlist = [] #THIS BE WHAT WE LOOP OVER LOL XD
    for ship in v.shipindices[:v.shipindices.index(highest)+1]:
        renderlist.append({'ship': ship.replace('_', ' ').capitalize(), 'form': "%s %s" % (f.pk, ship)})
    return renderlist

def highestship(f):
    highest = "freighters"
    for ship in v.shipindices:
        if f.__dict__[ship] > 0:
            highest = ship
    return highest

def longtimeformat(delta):
    days = delta.days
    timedeltaseconds = delta.seconds
    hours, remainder = divmod(timedeltaseconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days == 1:
        return '<p>Last seen: %(days)s day, %(hours)s hr ago</p>' % {'days':days,'hours':hours}
    elif days > 1:
        return '<p>Last seen: %s days ago</p>' % days
    elif hours == 0 and minutes < 10:
        return '<p style="color:green;">Online</p>'
    elif hours == 0:
        return '<p>Last seen: %s minutes ago</p>' % minutes
    else:
        return '<p>Last seen: %(hours)s hr %(minutes)s min ago</p>' % {'hours':hours,'minutes':minutes}
    
def lastonline(world):
    lastonline = world.lastloggedintime
    delta = v.now() - lastonline
    return longtimeformat(delta)




policyname = {
    'continental': True,
    'Africa': ['response'],
    'Latin America': ['response'],
    'Asia': ['response',
                'response2',
                'response3'],
    'Middle East': ['response']
}