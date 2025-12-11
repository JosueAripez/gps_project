# tracker/views.py
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Device, Geofence, Location, Alert
from .serializers import DeviceSerializer, GeofenceSerializer, LocationSerializer, AlertSerializer
from .utils import is_inside_geofence
from django.shortcuts import render
from django.conf import settings
import os, json
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Página principal (mapa)
def index(request):
    return render(request, 'tracker/index.html', {})

# ViewSets CRUD
class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

class GeofenceViewSet(viewsets.ModelViewSet):
    queryset = Geofence.objects.all()
    serializer_class = GeofenceSerializer

    def list(self, request, *args, **kwargs):
        print("Consulta API geofences")
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        data = self.request.data
        def parse_float(val):
            if isinstance(val, str):
                val = val.replace(',', '.')
            try:
                return float(val)
            except Exception:
                return 0.0
        center_lat = parse_float(data.get('center_lat'))
        center_lon = parse_float(data.get('center_lon'))
        radius_m = parse_float(data.get('radius_m'))
        serializer.save(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_m=radius_m
        )

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.all().order_by('-created_at')
    serializer_class = AlertSerializer

# Endpoint para recibir ubicaciones desde Postman
class LocationCreateView(APIView):
    """
    POST JSON esperado:
    {
      "device_identifier": "device123",
      "device_name": "Mi Telefono",
      "latitude": 19.4326,
      "longitude": -99.1332,
      "timestamp": "2025-10-13T08:00:00Z"  # optional
    }
    """
    def post(self, request):
        data = request.data
        device_identifier = data.get('device_identifier')
        device_name = data.get('device_name', 'Sin nombre')
        lat = data.get('latitude')
        lon = data.get('longitude')
        timestamp = data.get('timestamp')

        def parse_float(val):
            if isinstance(val, str):
                val = val.replace(',', '.')
            try:
                return float(val)
            except Exception:
                return 0.0

        if None in (device_identifier, lat, lon):
            return Response({"error":"Faltan campos: device_identifier, latitude, longitude"}, status=status.HTTP_400_BAD_REQUEST)

        device, _ = Device.objects.get_or_create(identifier=device_identifier, defaults={'name': device_name})

        try:
            ts = parse_datetime(timestamp) if timestamp else None
            if ts is None:
                ts = timezone.now()
        except Exception:
            ts = timezone.now()

        lat_f = parse_float(lat)
        lon_f = parse_float(lon)

        loc = Location.objects.create(device=device, latitude=lat_f, longitude=lon_f, timestamp=ts)

        geofences = Geofence.objects.all()
        inside_any = False
        checks = []
        for gf in geofences:
            inside, dist = is_inside_geofence(lat_f, lon_f, gf)
            checks.append({'geofence': gf.name, 'inside': inside, 'distance_m': dist, 'radius_m': gf.radius_m})
            if inside:
                inside_any = True

        alerts_created = []
        if not inside_any and geofences.exists():
            msg = f"Ubicación fuera de geocercas: ({lat_f},{lon_f})"
            alert = Alert.objects.create(location=loc, geofence=None, message=msg)
            alerts_created.append(AlertSerializer(alert).data)
        else:
            # Si está dentro de alguna geocerca, verifica si hay configuración de alerta
            for gf in geofences:
                inside, _ = is_inside_geofence(lat_f, lon_f, gf)
                if inside:
                    key = (device.identifier, str(gf.id))
                    email = ALERT_CONFIGS.get(key)
                    if email:
                        send_mail(
                            subject="Alerta de Geocerca",
                            message=f"El dispositivo {device.name} ({device.identifier}) entró en la geocerca '{gf.name}'.\nUbicación: {lat_f}, {lon_f}",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=True,
                        )

        try:
            export_dir = os.path.join(settings.BASE_DIR, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            file_path = os.path.join(export_dir, 'locations_log.json')
            record = {
                'device_identifier': device_identifier,
                'device_name': device_name,
                'latitude': lat_f,
                'longitude': lon_f,
                'timestamp': ts.isoformat(),
                'inside_any_geofence': inside_any,
                'checks': checks
            }
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            file_error = None
        except Exception as e:
            file_error = str(e)

        return Response({
            'location': LocationSerializer(loc).data,
            'inside_any_geofence': inside_any,
            'checks': checks,
            'alerts_created': alerts_created,
            'file_error': file_error
        }, status=status.HTTP_201_CREATED)

# Endpoint para recibir actualizaciones desde dispositivos
class DeviceUpdateLocationView(APIView):
    """
    POST JSON esperado:
    {
      "device_identifier": "device123",
      "device_name": "Mi Telefono",
      "latitude": 19.4326,
      "longitude": -99.1332,
      "timestamp": "2025-10-13T08:00:00Z"  # opcional
    }
    """
    def post(self, request):
        data = request.data
        device_identifier = data.get('device_identifier')
        device_name = data.get('device_name', 'Sin nombre')
        lat = data.get('latitude')
        lon = data.get('longitude')
        timestamp = data.get('timestamp')

        def parse_float(val):
            if isinstance(val, str):
                val = val.replace(',', '.')
            try:
                return float(val)
            except Exception:
                return 0.0

        if None in (device_identifier, lat, lon):
            return Response({"error": "Faltan campos: device_identifier, latitude, longitude"}, status=status.HTTP_400_BAD_REQUEST)

        device, _ = Device.objects.get_or_create(identifier=device_identifier, defaults={'name': device_name})

        try:
            ts = parse_datetime(timestamp) if timestamp else None
            if ts is None:
                ts = timezone.now()
        except Exception:
            ts = timezone.now()

        lat_f = parse_float(lat)
        lon_f = parse_float(lon)

        loc = Location.objects.create(device=device, latitude=lat_f, longitude=lon_f, timestamp=ts)

        return Response({
            'location': LocationSerializer(loc).data,
            'message': 'Ubicación actualizada correctamente'
        }, status=status.HTTP_201_CREATED)

# Endpoint para obtener última ubicación (para el mapa)
class LastLocationView(APIView):
    def get(self, request):
        loc = Location.objects.order_by('-received_at').first()
        if not loc:
            return Response({'detail':'No hay ubicaciones aún'}, status=status.HTTP_404_NOT_FOUND)
        return Response(LocationSerializer(loc).data)

class DeviceTrackView(APIView):
    """
    GET con parámetros:
      ?device_identifier=xxx&start=YYYY-MM-DDTHH:MM:SSZ&end=YYYY-MM-DDTHH:MM:SSZ
    Devuelve todas las ubicaciones del dispositivo en ese rango.
    """
    def get(self, request):
        device_identifier = request.GET.get('device_identifier')
        start = request.GET.get('start')
        end = request.GET.get('end')
        if not device_identifier or not start or not end:
            return Response({'error': 'Faltan parámetros'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            device = Device.objects.get(identifier=device_identifier)
        except Device.DoesNotExist:
            return Response({'error': 'Dispositivo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        start_dt = parse_datetime(start)
        end_dt = parse_datetime(end)
        if not start_dt or not end_dt:
            return Response({'error': 'Fechas inválidas'}, status=status.HTTP_400_BAD_REQUEST)
        locations = Location.objects.filter(
            device=device,
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        ).order_by('timestamp')
        data = [
            {
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'timestamp': loc.timestamp.isoformat()
            }
            for loc in locations
        ]
        return Response({'track': data})

ALERT_CONFIGS = {}  # { (device_identifier, geofence_id): email }

@method_decorator(csrf_exempt, name='dispatch')
class AlertConfigView(APIView):
    """
    POST: {device_identifier, geofence_id, email}
    """
    def post(self, request):
        device_identifier = request.data.get('device_identifier')
        geofence_id = request.data.get('geofence_id')
        email = request.data.get('email')
        if not device_identifier or not geofence_id or not email:
            return Response({'error': 'Faltan datos'}, status=400)
        ALERT_CONFIGS[(device_identifier, str(geofence_id))] = email
        return Response({'ok': True})
