# Django Imports
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.templatetags.static import static

# WaW Imports
from wawmembers.models import World, AgreementLog
from wawmembers.decorators import ajax_required

'''
Anything that needs interaction with the server outside of a page refresh.
'''

@ajax_required
def username(request):
    'Checks if a username exists already.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'username' in p:
            name = p['username']
            if User.objects.filter(username__iexact=name):
                return HttpResponse(False)
            else:
                return HttpResponse(True)


@ajax_required
def email(request):
    'Checks if an email exists already.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'email' in p:
            email = p['email']
            if User.objects.filter(email__iexact=email):
                return HttpResponse(False)
            else:
                return HttpResponse(True)


@ajax_required
def worldname(request):
    'Checks if a world name exists already.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'worldname' in p:
            name = p['worldname']
            if World.objects.filter(world_name__iexact=name):
                return HttpResponse(False)
            else:
                return HttpResponse(True)


@ajax_required
def agreementread(request):
    'Updates the read status of economic notifications.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'worldid' in p:
            worldid = p['worldid']
            try:
                world = World.objects.get(worldid=worldid)
            except:
                pass
            else:
                AgreementLog.objects.filter(owner=world).update(seen=True)
    return HttpResponse(True)


@ajax_required
def avatar(request):
    'Fetches avatar pic url.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'id' in p:
            name = p['id']
            imgloc = static('settings/avnf/'+name+'.gif')
            return HttpResponse(imgloc)


@ajax_required
def flag(request):
    'Fetches flag pic url.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'id' in p:
            name = p['id']
            imgloc = static('settings/avnf/'+name+'.gif')
            return HttpResponse(imgloc)


@ajax_required
def background(request):
    'Fetches background pic url.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'id' in p:
            name = p['id']
            imgloc = static('settings/bg/'+name+'.gif')
            return HttpResponse(imgloc)

@ajax_required
def personalship(request):
    'Fetches personal ship pic url.'
    if request.method == "GET":
        p = request.GET.copy()
        if 'id' in p:
            name = p['id']
            imgloc = static('settings/ps/'+name+'.gif')
            return HttpResponse(imgloc)
