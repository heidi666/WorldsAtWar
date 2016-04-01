# Django Imports
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache

# WaW Imports
from wawmembers.models import *

'''
Not much in this file: ban/delete functions and display of objects in the admin view.
'''

# World
def delete_user(modeladmin, request, queryset):
    for world in queryset:
        user = User.objects.get(id=world.worldid)
        user.is_active = False
        user.save()
        world.delete()

def ban_user(modeladmin, request, queryset):
    for world in queryset:
        banip = world.lastloggedinip
        user = User.objects.get(id=world.worldid)
        user.is_active = False
        user.save()
        world.delete()
    try: Ban.objects.create(address=banip, reason='Multying')
    except: pass

class WorldAdmin(admin.ModelAdmin):
    readonly_fields = ('resourceproduction',)
    fieldsets = (
        ('Meta', {
            'classes': ('wide',),
            'fields': (('worldid','donator', 'vacation'),'world_descriptor','user_name','world_name','world_desc',('creationtime',
                       'lastloggedintime'),('creationip','lastloggedinip'),'region','card','rumsoddium','backgroundpref')
        }),
        ('Economy', {
            'classes': ('collapse','wide',),
            'fields': ('econsystem', 'gdp', 'budget', 'growth', 'industrialprogram', 'resource', 'resourceproduction')
        }),
        ('Domestic', {
            'classes': ('collapse',),
            'fields': ('polsystem', 'contentment', 'stability', 'rebels','qol')
        }),
        ('Materials', {
            'classes': ('collapse','wide',),
            'fields': (('warpfuel','warpfuelprod'),('duranium','duraniumprod'),('tritanium','tritaniumprod'),
                       ('adamantium','adamantiumprod'),('salvdur','salvtrit','salvadam'),('freighter_inA','freighter_inB'),
                       ('freighter_inC','freighter_inD'),('freighter_inS','freightersinuse'))
        }),
        ('General Military', {
            'classes': ('collapse','wide'),
            'fields': ('millevel','turnresearched','timetonextadmiralty','noobprotect',('shipyards','shipyardsinuse'),
                       ('warsperturn','declaredwars'),('warprotection','abovegdpprotection'),'brokenwarprotect',
                       ('startpower','powersent'),'warpoints','shipsortprefs',('flagshiptype','flagshiplocation'),'flagshipname')
        }),
        ('Fleet A', {
            'classes': ('collapse','wide',),
            'fields': ('fleetname_inA',('fleet_inA_training','fleet_inA_weariness'),'fighters_inA','corvette_inA',
                       'light_cruiser_inA','destroyer_inA','frigate_inA','heavy_cruiser_inA','battlecruiser_inA',
                       'battleship_inA','dreadnought_inA')
        }),
        ('Fleet B', {
            'classes': ('collapse','wide',),
            'fields': ('fleetname_inB',('fleet_inB_training','fleet_inB_weariness'),'fighters_inB','corvette_inB',
                       'light_cruiser_inB','destroyer_inB','frigate_inB','heavy_cruiser_inB','battlecruiser_inB',
                       'battleship_inB','dreadnought_inB')
        }),
        ('Fleet C', {
            'classes': ('collapse','wide',),
            'fields': ('fleetname_inC',('fleet_inC_training','fleet_inC_weariness'),'fighters_inC','corvette_inC',
                       'light_cruiser_inC','destroyer_inC','frigate_inC','heavy_cruiser_inC','battlecruiser_inC',
                       'battleship_inC','dreadnought_inC')
        }),
        ('Fleet D', {
            'classes': ('collapse','wide',),
            'fields': ('fleetname_inD',('fleet_inD_training','fleet_inD_weariness'),'fighters_inD','corvette_inD',
                       'light_cruiser_inD','destroyer_inD','frigate_inD','heavy_cruiser_inD','battlecruiser_inD',
                       'battleship_inD','dreadnought_inD')
        }),
        ('Hangars', {
            'classes': ('collapse','wide',),
            'fields': ('fleet_inH_training','fighters_inH','corvette_inH','light_cruiser_inH','destroyer_inH',
                       'frigate_inH','heavy_cruiser_inH','battlecruiser_inH', 'battleship_inH','dreadnought_inH')
        }),
        ('Staging', {
            'classes': ('collapse','wide',),
            'fields': ('fleet_inS_training','fighters_inS','corvette_inS','light_cruiser_inS','destroyer_inS',
                       'frigate_inS','heavy_cruiser_inS','battlecruiser_inS', 'battleship_inS','dreadnought_inS')
        }),
        ('Alliance', {
            'classes': ('collapse','wide',),
            'fields': ('alliance','alliancepaid','officer','leader')
        }),
    )
    filter_horizontal = ('declaredwars',)
    list_display = ('world_name', 'user_name', 'worldid', 'lastloggedinip')
    search_fields = ['world_name','user_name','lastloggedinip']
    actions = [delete_user, ban_user]

admin.site.register(World, WorldAdmin)


# Alliance
class MemberInline(admin.TabularInline):
    model = World
    fk_name = 'alliance'
    fields = ('worldid','user_name','world_name','alliance','alliancepaid','officer','leader')
    extra = 0
    verbose_name = 'member'
    can_delete = False

class BankInline(admin.TabularInline):
    model = BankLog
    fk_name = 'alliance'
    fields = ('world', 'displayaction', 'amount', 'before', 'after', 'datetime')
    readonly_fields = ('world', 'displayaction', 'amount', 'before', 'after', 'datetime')
    extra = 0
    can_delete = False

class AllianceAdmin(admin.ModelAdmin):
    inlines = [
        MemberInline,
        BankInline,
    ]
    filter_horizontal = ('invites',)

admin.site.register(Alliance, AllianceAdmin)


# Spy
class SpyAdmin(admin.ModelAdmin):
    list_display = ('owner', 'location')
    search_fields = ['owner__world_name','location__world_name']

admin.site.register(Spy, SpyAdmin)


# NewsItem

admin.site.register(NewsItem)


# ActionNewsItem
class ActionNewsItemAdmin(admin.ModelAdmin):
    list_display = ('target', 'content')
    search_fields = ['target__world_name']

admin.site.register(ActionNewsItem, ActionNewsItemAdmin)


# Task

admin.site.register(Task)


# Comm
class CommAdmin(admin.ModelAdmin):
    list_display = ('target', 'sender')
    search_fields = ['target__world_name','sender__world_name']

admin.site.register(Comm, CommAdmin)


# Sent Comm
admin.site.register(SentComm)


# War

admin.site.register(War)


#GDP Sales
class GDPSaleAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('seller', 'buyer', 'geuamount', 'gdpamount', 'id',)
    search_fields = ['seller', 'buyer', 'id',]

admin.site.register(GDPSale, GDPSaleAdmin)

class GDPThresholdAdmin(admin.ModelAdmin):
    list_display = ('target', 'buythreshold', 'sellthreshold',)
    search_fields = ['target',]
admin.site.register(GDPSaleThresholdManager, GDPThresholdAdmin)
# Trade

admin.site.register(Trade)


# Announcement

admin.site.register(Announcement)


# Agreement
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver')
    search_fields = ['sender__world_name','receiver__world_name']

admin.site.register(Agreement, AgreementAdmin)


# Resource Logs
admin.site.register(ResourceLog)


# War Logs
admin.site.register(WarLog)


# Alliance Bank Logs

admin.site.register(BankLog)


# Alliance Member Logs

admin.site.register(AllianceLog)


# Agreement Logs

admin.site.register(AgreementLog)


# Global data

admin.site.register(GlobalData)


# Bans

def clear_ban(modeladmin, request, queryset):
    for ban in queryset:
        cache.delete('BAN:'+ban.address)
        ban.delete()

class BanAdmin(admin.ModelAdmin):

    def get_actions(self, request):
        actions = super(BanAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    actions = [clear_ban]
    search_fields = ['address']

admin.site.register(Ban, BanAdmin)
