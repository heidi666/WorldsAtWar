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
    fieldsets = (
        ('Meta', {
            'classes': ('wide',),
            'fields': ('world_descriptor', 'user','name','world_desc',('creationtime',
                       'lastloggedintime'),('creationip','lastloggedinip'),'sector','rumsoddium','backgroundpref')
        }),
        ('Economy', {
            'classes': ('collapse','wide',),
            'fields': ('econsystem', 'gdp', 'budget', 'growth')
        }),
        ('Domestic', {
            'classes': ('collapse',),
            'fields': ('polsystem', 'contentment', 'stability', 'rebels','qol')
        }),
        ('Materials', {
            'classes': ('collapse','wide',),
            'fields': (('warpfuel','warpfuelprod'),('duranium','duraniumprod'),('tritanium','tritaniumprod'),
                       ('adamantium','adamantiumprod'),('salvdur','salvtrit','salvadam'),('freighters', 'freightersinuse'))
        }),
        ('General Military', {
            'classes': ('collapse','wide'),
            'fields': ('millevel','turnresearched','timetonextadmiralty','noobprotect',('shipyards','productionpoints'),
                       ('warsperturn','declaredwars'),('warprotection','abovegdpprotection'),'brokenwarprotect',
                       ('startpower','powersent'),'warpoints','shipsortprefs',('flagshiptype'),'flagshipname')
        }),
        ('Alliance', {
            'classes': ('collapse','wide',),
            'fields': ('alliance','alliancepaid','officer','leader')
        }),
    )
    filter_horizontal = ('declaredwars',)
    list_display = ('name', 'user', 'pk', 'lastloggedinip')
    search_fields = ['name','lastloggedinip']
    actions = [delete_user, ban_user]

admin.site.register(World, WorldAdmin)

admin.site.register(preferences)

admin.site.register(fleet)

admin.site.register(shipqueue)

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

# Trade

admin.site.register(Trade)


# Announcement

admin.site.register(Announcement)


# Resource Logs
admin.site.register(ResourceLog)


# War Logs
admin.site.register(Warlog)


# Alliance Bank Logs

admin.site.register(BankLog)


# Alliance Member Logs

admin.site.register(AllianceLog)


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


class CookieAdmin(admin.ModelAdmin):
    list_display = ('LoggedIn', 'Match', 'date')

admin.site.register(SecurityCookie, CookieAdmin)
