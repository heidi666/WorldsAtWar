# Django Imports
from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static

# WaW Imports
from wawmembers.models import World, Comm, NewsItem, ActionNewsItem, AgreementLog, GlobalData
import wawmembers.variables as v

'''
Changes to the base template.
'''

register = template.Library()


def lowqolcs(context):
    'Additional punishment for low QOL.'

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        return ''

    if world.qol < -80:
        toreturn = '<style>body {font-family: "Comic Sans MS", cursive, sans-serif;}</style>'
    else:
        toreturn = ''

    return mark_safe(toreturn)

register.simple_tag(lowqolcs, takes_context=True)


def bgchoice(context):

    background = GlobalData.objects.get(pk=1).turnbackground

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        return static('backgrounds/%s.gif' % background)
    else:
        if world.backgroundpref == -1:
            return static('backgrounds/%s.gif' % v.background())
        elif world.backgroundpref == -2:
            return static('backgrounds/%s.gif' % background)
        else:
            return static('backgrounds/%s.gif' % world.backgroundpref)

register.simple_tag(bgchoice, takes_context=True)


def comms_quantity(context):

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        return ''

    unreadquantity = Comm.objects.filter(target=world, seen=False).count()
    commsquantity = Comm.objects.filter(target=world).count()

    if unreadquantity != 0:
        toreturn = '(<i>%d</i>, %d)' % (unreadquantity, commsquantity)
    elif commsquantity != 0:
        toreturn = '(%d)' % commsquantity
    else:
        toreturn = ''

    return mark_safe(toreturn)

register.simple_tag(comms_quantity, takes_context=True)


def news_quantity(context):

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        return ''

    newsquantity = NewsItem.objects.filter(target=world).count()
    unreadnews = NewsItem.objects.filter(target=world, seen=False).count()

    actionnewsquantity = ActionNewsItem.objects.filter(target=world).count()
    unreadactionnews = ActionNewsItem.objects.filter(target=world, seen=False).count()

    unread = unreadnews + unreadactionnews
    total = newsquantity + actionnewsquantity

    if unread != 0:
        toreturn = '(<i>%d</i>, %d)' % (unread, total)
    elif total != 0:
        toreturn = '(%d)' % total
    else:
        toreturn = ''

    return mark_safe(toreturn)

register.simple_tag(news_quantity, takes_context=True)


def agreementlog_quantity(context):

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        return ''

    total = AgreementLog.objects.filter(owner=world).count()
    unread = AgreementLog.objects.filter(owner=world, seen=False).count()

    if unread != 0:
        toreturn = '(<i>%d</i>, %d)' % (unread, total)
    elif total != 0:
        toreturn = '(%d)' % total
    else:
        toreturn = ''

    return mark_safe(toreturn)

register.simple_tag(agreementlog_quantity, takes_context=True)


def servertime():
    return v.now().strftime('%H:%M:%S')

register.simple_tag(servertime)


def policieschoice(context, js):
    'Choose what the policies button does.'

    request = context['request']
    try:
        world = World.objects.get(worldid=request.user.id)
    except:
        toreturn = '<a href="/policies/economics">Policies</a>'
    else:
        if world.policypref == 'econ':
            toreturn = '<a href="/policies/economics">Policies</a>'
        elif world.policypref == 'domestic':
            toreturn = '<a href="/policies/domestic">Policies</a>'
        elif world.policypref == 'diplomacy':
            toreturn = '<a href="/policies/diplomacy">Policies</a>'
        elif world.policypref == 'military':
            toreturn = '<a href="/policies/fleet">Policies</a>'
        elif world.policypref == 'js' and js == False:
            toreturn = '<a href="/policies/economics">Policies</a>'
        elif world.policypref == 'js' and js == True:
            toreturn = '<a href="#" class="sidebartrigger" id="links">Policies</a>' + \
                       '<div class="tip" id="links">' + \
                           '<center>' + \
                           '<a href="/policies/economics">Economic</a>' + \
                           '<a href="/policies/domestic">Domestic</a>' + \
                           '<a href="/policies/diplomacy">Diplomacy</a>' + \
                           '<a href="/policies/fleet">Fleet</a>' + \
                         '</center>' + \
                       '</div>'

    return mark_safe(toreturn)

register.simple_tag(policieschoice, takes_context=True)
