from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Device, Location, Geofence, AlertSubscription
from .serializers import DeviceSerializer, LocationSerializer, GeofenceSerializer, AlertSubscriptionSerializer
from django.utils.dateparse import parse_datetime
from django.core.mail import send_mail
from django.conf import settings
import math
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Haversine para distancia en metros
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

class GeofenceViewSet(viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer

class AlertSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = AlertSubscription.objects.all()
    serializer_class = AlertSubscriptionSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    # Endpoint para recibir actualizaciones desde dispositivos - POST simple
    # Alternativa: crear una APIView para validar datos


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone

@api_view(["POST"])
@permission_classes([AllowAny])  # Ajusta según necesites auth
def receive_location(request):
    """
    Espera JSON:
    {
      "device_id": "imei1234",
      "latitude": 19.123,
      "longitude": -99.123,
      "timestamp": "2025-11-20T18:45:00Z",
      "speed": 12.3
    }
    """
    data = request.data
    device_id = data.get("device_id")
    lat = data.get("latitude")
    lng = data.get("longitude")
    ts = data.get("timestamp")
    speed = data.get("speed", None)

    if not all([device_id, lat, lng, ts]):
        return Response({"error": "Faltan campos"}, status=status.HTTP_400_BAD_REQUEST)

    device, _ = Device.objects.get_or_create(identifier=device_id, defaults={"name": device_id})
    try:
        dt = parse_datetime(ts)
        if dt is None:
            # si no viene con timezone, asumir ahora
            dt = timezone.now()
    except Exception:
        dt = timezone.now()

    loc = Location.objects.create(device=device, latitude=float(lat), longitude=float(lng), timestamp=dt, speed=speed)

    # Emitir por WebSocket a consumidores ligados a este device:
    channel_layer = get_channel_layer()
    payload = {
        "type": "new_location",
        "device": device.identifier,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": loc.timestamp.isoformat(),
        "speed": loc.speed,
    }
    # Nombre de grupo: "device_{identifier}"
    async_to_sync(channel_layer.group_send)(f"device_{device.identifier}", {"type": "location.message", "text": json.dumps(payload)})

    # Revisar geocercas y generar alertas
    check_geofences_and_alert(device, loc)

    serializer = LocationSerializer(loc)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def check_geofences_and_alert(device, location):
    """
    Checa geocercas: si está fuera/entrando, manda mail.
    Estrategia simple: para cada geocerca suscrita al dispositivo, calculamos distancia
    y si > radius entonces decir que está fuera (o dentro según lo necesario).
    Podrías mantener estado previo (within/outside) para evitar spam - simple ejemplo no lo hace.
    """
    subs = AlertSubscription.objects.filter(device=device, active=True)
    for s in subs:
        gf = s.geofence
        dist = haversine(location.latitude, location.longitude, gf.center_lat, gf.center_lng)
        inside = dist <= gf.radius_m
        subject = f"Alerta geocerca: {device.name} {'ENTRÓ' if inside else 'SALIO'} {gf.name}"
        message = f"Dispositivo: {device}\nGeocerca: {gf.name}\nDentro: {inside}\nDistancia(m): {dist:.2f}\nFecha: {location.timestamp.isoformat()}"
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [s.email], fail_silently=False)
        except Exception as e:
            # en producción, loggear
            print("Error enviando correo:", e)



from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

def map_view(request):
    devices = Device.objects.all()
    return render(request, "tracker/map.html", {"devices": devices})

def history_view(request):
    # página que pide device y rango y hace fetch de /api/locations/?device=...&start=...&end=...
    devices = Device.objects.all()
    return render(request, "tracker/history.html", {"devices": devices})

def alerts_ui(request):
    geofences = Geofence.objects.all()
    devices = Device.objects.all()
    return render(request, "tracker/alerts.html", {"devices": devices, "geofences": geofences})


from rest_framework import filters

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        device = self.request.query_params.get("device")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if device:
            qs = qs.filter(device__identifier=device)
        if start:
            qs = qs.filter(timestamp__gte=start)
        if end:
            qs = qs.filter(timestamp__lte=end)
        return qs
