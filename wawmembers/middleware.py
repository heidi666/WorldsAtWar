# Django Imports
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

# Python Imports
import datetime
import base64

# WaW Imports
from wawmembers.models import Ban, SecurityCookie, World
import wawmembers.variables as v

'''
Functions that run for every single request.
'''

class MaintenanceCheckMiddleware(object):
    'Checks for maintenance mode.'

    def process_request(self, request):
        if v.maintenance:
            return render(request, 'maintenance.html')
        else:
            return None


class SecurityCookieMiddleware(object):
    'Sets and checks the security cookie.'

    def __init__(self):
        self.ENABLED = getattr(settings,'SCOOKIE_ENABLED', False)
        if not self.ENABLED:
            raise MiddlewareNotUsed("Security Cookie not enabled in settings.py")

    def process_response(self, request, response):
        try:
            if request.user.id is None:
                return response
            else:
                if not request.COOKIES.get("sessionid2"):
                    # set cookie
                    response.set_cookie("sessionid2", value=base64.b64encode(str(request.user.id)), max_age=365*24*60*60)
                else:
                    check = request.COOKIES.get("sessionid2")
                    if check != base64.b64encode(str(request.user.id)):
                        w1 = World.objects.get(worldid=request.user.id)
                        w2 = World.objects.get(worldid=base64.b64decode(str(check)))
                        # create alert
                        match = SecurityCookie(LoggedIn=w1, LoggedInB64=base64.b64encode(str(request.user.id)), Match=w2, MatchB64=check)
                        match.save()
                return response
        except AttributeError:
            return response


class BanCheckMiddleware(object):
    'Checks for bans.'

    def __init__(self):
        """
        Middleware init is called once per server on startup - do the heavy
        lifting here.
        """
        # If disabled or not enabled raise MiddleWareNotUsed so django
        # processes next middleware.
        self.ENABLED = getattr(settings, 'BANS_ENABLED', False)
        self.DEBUG = getattr(settings, 'BANS_DEBUG', False)

        if not self.ENABLED:
            raise MiddlewareNotUsed("bans are not enabled via settings.py")

        if self.DEBUG:
            print "Bans status = enabled"

        # Populate various 'banish' buckets
        for ban in Ban.objects.all():
            if self.DEBUG:
                print ban
            cache.add('BAN:'+ban.address, '1', None)

    def process_request(self, request):

        ip = request.META['REMOTE_ADDR']
        if (not ip or ip == '127.0.0.1') and 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']

        if self.DEBUG:
            print "Got request from: %s" % ip

        if self.is_banned(ip):
            ban = Ban.objects.get(address=ip)
            return render(request, 'ban.html', {'reason': ban.reason})

    def is_banned(self, ip):
        # if a key exists we know the user is banned.
        return cache.get('BAN:'+ip)
