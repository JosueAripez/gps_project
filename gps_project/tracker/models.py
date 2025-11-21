from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)  # id que mandan los dispositivos
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"

class Location(models.Model):
    device = models.ForeignKey(Device, related_name="locations", on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField()  # enviado por el dispositivo
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.device} @ {self.latitude},{self.longitude} at {self.timestamp}"

class Geofence(models.Model):
    name = models.CharField(max_length=100)
    center_lat = models.FloatField()
    center_lng = models.FloatField()
    radius_m = models.FloatField(help_text="Radio en metros")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.center_lat},{self.center_lng} r={self.radius_m}m)"

class AlertSubscription(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Alerta {self.email} - {self.device} - {self.geofence}"
