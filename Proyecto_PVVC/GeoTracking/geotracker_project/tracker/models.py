# tracker/models.py
from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"

class Geofence(models.Model):
    name = models.CharField(max_length=100)
    center_lat = models.FloatField()
    center_lon = models.FloatField()
    radius_m = models.FloatField(help_text="Radio en metros")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Validación de rango de latitud y longitud
        if not (-90 <= self.center_lat <= 90):
            raise ValueError("Latitud fuera de rango")
        if not (-180 <= self.center_lon <= 180):
            raise ValueError("Longitud fuera de rango")

    def __str__(self):
        return f"{self.name} ({self.radius_m} m)"

class Location(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField()   # enviado por cliente o generado en servidor
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.identifier}: ({self.latitude},{self.longitude})"

class Alert(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='alerts')
    geofence = models.ForeignKey(Geofence, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.message[:50]}"
