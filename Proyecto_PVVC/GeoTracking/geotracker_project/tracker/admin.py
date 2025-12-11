# tracker/admin.py
from django.contrib import admin
from .models import Device, Geofence, Location, Alert

admin.site.register(Device)
admin.site.register(Geofence)
admin.site.register(Location)
admin.site.register(Alert)
