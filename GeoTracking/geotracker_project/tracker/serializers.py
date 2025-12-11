# tracker/serializers.py
from rest_framework import serializers
from .models import Device, Geofence, Location, Alert

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class GeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geofence
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = '__all__'  # incluye todos los campos originales
        extra_fields = ['device_name']

    def get_device_name(self, obj):
        return obj.device.name if obj.device else ''

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'
