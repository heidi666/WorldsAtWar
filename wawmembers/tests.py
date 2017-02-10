from django.test import TestCase
from wawmembers.forms import *
from wawmembers.models import *
from wawmembers.views import *
import wawmembers.variables as v


def exchangetest():
    w = World.objects.get(pk=1)
    am = w.controlled_fleets.all().filter(sector="amyntas")
    init = {}
    for ship in v.shipindices[:v.shipindices.index('battlecruisers')+1]:
        init.update({'id_%s %s' % (am[0].pk, ship): 100})
        init.update({'id_%s %s' % (am[1].pk, ship): 100})
    b = Shipexchangeform(am[0], am[1], data=init)
    b
    print b
    print dir(b)
    print b.is_valid()


# Create your tests here.
