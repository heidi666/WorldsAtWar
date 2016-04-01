# Django Imports
from django import template
from django.utils.safestring import mark_safe

'''
HTML for ship building options.
'''

register = template.Library()

def shipbuildtype(shiptype, pref):

    if shiptype == 1:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountfig" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildfighter" value="Fighter"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountfig" size="3" style="font-family:monospace">'''
    elif shiptype == 2:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountcor" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildcorvette" value="Corvette"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountcor" size="3" style="font-family:monospace">'''
    elif shiptype == 3:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountlcr" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildlightcruiser" value="Light Cruiser"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountlcr" size="3" style="font-family:monospace">'''
    elif shiptype == 4:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountdes" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="builddestroyer" value="Destroyer"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountdes" size="3" style="font-family:monospace">'''
    elif shiptype == 5:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountfri" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildfrigate" value="Frigate"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountfri" size="3" style="font-family:monospace">'''
    elif shiptype == 6:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amounthcr" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildheavycruiser" value="Heavy Cruiser"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amounthcr" size="3" style="font-family:monospace">'''
    elif shiptype == 7:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountbcr" value="1" size="3" style="font-family:monospace">&nbsp;
            <input type="submit" name="buildbattlecruiser" value="Battlecruiser"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountbcr" size="3" style="font-family:monospace">'''
    elif shiptype == 8:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountbsh" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="buildbattleship" value="Battleship"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountbsh" size="3" style="font-family:monospace">'''
    elif shiptype == 9:
        if pref == 'ind':
            toreturn = '''<input type="text" name="amountdre" value="1" size="3" style="font-family:monospace">&nbsp;
                <input type="submit" name="builddreadnought" value="Dreadnought"  class="button"/>'''
        else:
            toreturn = '''<input type="text" id="amountdre" size="3" style="font-family:monospace">'''

    return mark_safe(toreturn)

register.simple_tag(shipbuildtype)
