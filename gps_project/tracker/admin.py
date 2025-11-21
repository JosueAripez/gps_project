from django.contrib import admin
from .models import Device, Location, Geofence, AlertSubscription


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'owner', 'created_at')
    search_fields = ('name', 'identifier')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('device', 'latitude', 'longitude', 'speed', 'timestamp')
    list_filter = ('device',)
    search_fields = ('device__name', 'device__identifier')


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'center_lat', 'center_lng', 'radius_m', 'created_by')
    search_fields = ('name',)


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('device', 'geofence', 'email', 'active', 'created_at')
    list_filter = ('active', 'device', 'geofence')
    search_fields = ('email',)
