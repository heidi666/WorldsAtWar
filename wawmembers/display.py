'''
Converts numbers to text descriptions.
'''

def training_display(current, maximum):
    try:
        ratio = float(current)/float(maximum)
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

def weariness_display(current):
    if current == 200:
        return 'Raring to go'
    elif 160 <= current < 200:
        return 'Fresh'
    elif 120 <= current < 160:
        return 'Ready'
    elif 80 <= current < 120:
        return 'Tired'
    elif 40 <= current < 80:
        return 'Weary'
    elif current < 40:
        return 'Exhausted'

def region_display(region):
    if region == 'A':
        return 'Amyntas'
    elif region == 'B':
        return 'Bion'
    elif region == 'C':
        return 'Cleon'
    elif region == 'D':
        return 'Draco'
    elif region == 'S':
        return 'Staging'
    elif region == 'H':
        return 'Hangars'

def trade_display(resource):
    if resource == 1:
        return 'Abbasid Salmonite'
    elif resource == 2:
        return 'Personal Drones'
    elif resource == 3:
        return 'Ice Moss'
    elif resource == 4:
        return 'Hyperfibers'
    elif resource == 5:
        return 'Dyon Crystals'
    elif resource == 6:
        return 'Small Arms'
    elif resource == 7:
        return 'Boson Condensate'
    elif resource == 8:
        return 'Chronimium Gas'
    elif resource == 9:
        return 'Tetramite Ore'
    elif resource == 10:
        return 'Maintenance Spiders'
    elif resource == 11:
        return 'Entertainment Holos'
    elif resource == 12:
        return 'Quantum Dot CPUs'

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
