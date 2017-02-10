# Django Imports
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.core.exceptions import ObjectDoesNotExist

# Python Imports
import datetime as time

# WaW Imports
from wawmembers.models import World, ActionNewsItem
import wawmembers.variables as v

'''
Misc checks that apply to more than one function.
'''

def ajax_required(f):
    'General ajax wrap function'
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def world_required(f):
    'Checks if the user has a world, for redirect purposes.'
    def wrap(request, *args, **kwargs):
        try:
            world = World.objects.get(user=request.user)
        except ObjectDoesNotExist:
            return redirect('new_world')
        else:
            if world.preferences.vacation:
                return render(request, 'vacation.html')
            else:
                return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def noaction_required(f):
    'Redirects user to home page if action news older than a day unaddressed.'
    def wrap(request, *args, **kwargs):
        world = World.objects.get(user=request.user)
        if ActionNewsItem.objects.filter(target=world, datetime__lt=v.now()-time.timedelta(days=1)).exists():
            from wawmembers.views import main
            return main(request, message='You have events more than a day old that need to be addressed! <br> Go to the news page.')
        else:
            return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
