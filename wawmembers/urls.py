# Django Imports
from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

# WaW Imports
from wawmembers import views, interactions, news, policies, ajax

'''
Dispatches URL requests to functions.
'''

urlpatterns = patterns('',
    url(r'^index/$', views.index, name='index'),
    url(r'^main/$', views.main, name='main'),
    url(r'^main/spies/$', views.spies, name='spies'),
    url(r'^main/warlogs/$', views.warlogs, name='warlogs'),
    url(r'^main/reslogs/$', views.reslogs, name='reslogs'),
    url(r'^main/tradecentre/$', views.tradecentre, name='tradecentre'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^worldnews/$', news.world_news, name='world_news'),
    url(r'^communiques/$', views.communiques, name='communiques'),
    url(r'^communiques/sent$', views.sentcomms, name='sentcomms'),
    url(r'^tasks/$', views.tasks, name='tasks'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^stats/(?P<page>\d+)/$', views.statspage, name='statspage'),
    url(r'^world/(?P<userid>\d+)/$', interactions.stats_ind, name='stats_ind'),
    url(r'^newworld/$', views.new_world, name='new_world'),
    url(r'^federations/$', views.alliances, name='alliances'),
    url(r'^federations/(?P<page>\d+)/$', views.alliancespage, name='alliancespage'),
    url(r'^federation/(?P<allid>\d+)/$', views.alliances_ind, name='alliances_ind'),
    url(r'^federation/(?P<allid>\d+)/banklogs/$', views.alliances_logs, name='alliances_logs'),
    url(r'^federation/(?P<allid>\d+)/memberlogs/$', views.alliances_memberlogs, name='alliances_memberlogs'),
    url(r'^federation/(?P<allid>\d+)/stats/$', views.alliances_stats, name='alliances_stats'),
    url(r'^federation/(?P<allid>\d+)/admin/$', views.alliances_admin, name='alliances_admin'),
    url(r'^federations/new/$', views.new_alliance, name='new_alliance'),
    url(r'^policies/$', RedirectView.as_view(url='/policies/economics', permanent=True)),
    url(r'^policies/economics/$', policies.policies_econ, name='policies_econ'),
    url(r'^policies/domestic/$', policies.policies_domestic, name='policies_domestic'),
    url(r'^policies/diplomacy/$', policies.policies_diplomacy, name='policies_diplomacy'),
    url(r'^policies/fleet/$', policies.policies_military, name='policies_military'),
    url(r'^trades/$', views.trades, name='trades'),
    url(r'^trades/new$', views.newtrade, name='newtrade'),
    url(r'^galacticnews/$', views.galacticnews, name='galactic_news'),
    url(r'^donate/$', TemplateView.as_view(template_name='donate.html'), name='donate'),
    url(r'^irc/$', TemplateView.as_view(template_name='irc.html'), name='irc'),
    url(r'^legal/$', TemplateView.as_view(template_name='legal.html'), name='legal'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    # GDP Sale Mechanism
    url(r'^gdp/$', views.gdphome, name="gdphome"),
    url(r'^gdp/offers/$', views.gdpoffers, name="gdpoffers"),
    url(r'^gdp/makeoffer/$', views.gdpmakeoffer, name='gdpmakeoffer'),
    url(r'^gdp/offers/(?P<saleid>\d+)/accept/$', views.acceptgdpsale, name="acceptgdpsale"),
    url(r'^gdp/offers/(?P<saleid>\d+)/deny/$', views.denygdpsale, name="denygdpsale"),
    url(r'^gdp/offers/(?P<saleid>\d+)/revoke/$', views.revokegdpsale, name='revokegdpsale'),
    # ajax
    url(r'^ajax/username/$', ajax.username, name='ajaxusername'),
    url(r'^ajax/email/$', ajax.email, name='ajaxemail'),
    url(r'^ajax/worldname/$', ajax.worldname, name='ajaxworldname'),
    url(r'^ajax/agreementread/$', ajax.agreementread, name='ajaxagreementread'),
    url(r'^ajax/avatar/$', ajax.avatar, name='ajaxavatar'),
    url(r'^ajax/flag/$', ajax.flag, name='ajaxflag'),
    url(r'^ajax/background/$', ajax.background, name='ajaxbackground'),
    url(r'^ajax/personalship/$', ajax.personalship, name='ajaxpersonalship'),
    # misc redirects
    url(r'^forum/$', RedirectView.as_view(url='/forums', permanent=True)),
    # url(r'^video/$', TemplateView.as_view(template_name='video.html'), name='video'),
    url(r'^snake/$', TemplateView.as_view(template_name='snake.html'), name='snake'),
    url(r'^guide/$', RedirectView.as_view(url='http://wawgame.eu/forums/index.php?topic=16.0', permanent=True), name='guide'),
    url(r'^rules/$', RedirectView.as_view(url='http://wawgame.eu/forums/index.php?topic=650.0', permanent=True), name='rules'),
)
