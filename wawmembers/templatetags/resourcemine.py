# Django Imports
from django import template
from django.utils.safestring import mark_safe

'''
Name and description for trade resources.
'''

register = template.Library()

def resourcemine(resource):
    if resource == 1:
        name = 'Salmonite Factory'
        description = 'Abbasid Salmonite is a vat-grown synthetic food that approximates the taste of Old Terran salmon. A galactic delicacy.'
    elif resource == 2:
        name = 'Drone Factory'
        description = 'Personal Drones perform a variety of functions for the elderly and infirm, like cooking and cleaning.'
    elif resource == 3:
        name = 'Ice Moss Extractor'
        description = 'Ice Moss is an exquisite spice that grows only on the coldest areas of Amyntasian moons.'
    elif resource == 4:
        name = 'Hyperfiber Factory'
        description = 'Hyperfibers are nanoengineered strands of molecular carbon, used to create many light, strong, and heat-resistant materials.'
    elif resource == 5:
        name = 'Crystal Factory'
        description = 'Dyon Crystals are synthetic crystals used to regulate domestic warp applications, and many other high-power processes.'
    elif resource == 6:
        name = 'Small Arms Factory'
        description = 'There is no shortage of petty criminal scum in the galaxy. Stop them dead in their tracks with these Bion-produced weapons.'
    elif resource == 7:
        name = 'Boson Condenser'
        description = 'Boson Condensate is an exotic form of matter used for high density backup energy storage.'
    elif resource == 8:
        name = 'Chronimium Gas Extractor'
        description = 'Chronimium Gas, when purified and processed, is used as a moderator for various high-power reactions.'
    elif resource == 9:
        name = 'Tetramite Ore Extractor'
        description = 'Tetramite is a versatile material used in all sorts of domestic construction projects.'
    elif resource == 10:
        name = 'Spider Factory'
        description = 'Maintenance Spiders are small machines that crawl over structures and repair everything from frayed wires to burst pipes.'
    elif resource == 11:
        name = 'Holo Studio'
        description = 'Draco makes various entertainment holos that allow the viewer to be a part of the latest action/detective/salacious story.'
    elif resource == 12:
        name = 'Quantum CPU Factory'
        description = 'Quantum Dot CPUs are the most advanced kind of processor currently in production, with a vast array of applications.'

    toreturn = '<td class="bigger" colspan="2">Build %s</td></tr><tr><td colspan="2">%s</td>' % (name, description)
    return mark_safe(toreturn)

register.simple_tag(resourcemine)
