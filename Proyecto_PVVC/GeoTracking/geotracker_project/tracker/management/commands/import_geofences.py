# tracker/management/commands/import_geofences.py
from django.core.management.base import BaseCommand
from tracker.models import Geofence
import json, os
from django.conf import settings
import re

class Command(BaseCommand):
    help = 'Import geofences from exports/geofences_import.json'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'exports', 'geofences_import.json')
        # Geocerca de prueba
        test_geofence = {
            "name": "PruebaManual",
            "center_lat": "41.867554",
            "center_lon": "116.665028",
            "radius_m": "5000"
        }
        # Importa la geocerca de prueba antes del archivo
        def parse_float(val):
            if isinstance(val, str):
                val = val.strip().replace(',', '.')
                # Busca el primer número decimal válido en el string
                match = re.search(r'-?\d+\.\d+', val)
                if match:
                    val = match.group(0)
                else:
                    # Si no hay punto decimal, busca solo número entero
                    match = re.search(r'-?\d+', val)
                    if match:
                        val = match.group(0)
            try:
                return float(val)
            except Exception:
                return 0.0

        lat = parse_float(test_geofence.get('center_lat'))
        lon = parse_float(test_geofence.get('center_lon'))
        radius = parse_float(test_geofence.get('radius_m'))
        # Debug: imprime los valores de la geocerca de prueba
        print(f"Importando TEST: name={test_geofence.get('name')}, lat={lat}, lon={lon}, radius={radius}")
        Geofence.objects.update_or_create(
            name=test_geofence.get('name'),
            defaults={
                'center_lat': lat,
                'center_lon': lon,
                'radius_m': radius,
            }
        )

        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f'No existe {path}'))
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 1  # Ya se importó la de prueba
        for item in data:
            lat = parse_float(item.get('center_lat'))
            lon = parse_float(item.get('center_lon'))
            radius = parse_float(item.get('radius_m'))
            # Debug: imprime los valores antes de guardar
            print(f"Importando: name={item.get('name')}, lat={lat}, lon={lon}, radius={radius}")

            Geofence.objects.update_or_create(
                name=item.get('name'),
                defaults={
                    'center_lat': lat,
                    'center_lon': lon,
                    'radius_m': radius,
                }
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Importadas/actualizadas {count} geofences'))

        # Mostrar todas las geocercas existentes tras la importación
        all_geofences = Geofence.objects.all()
        for gf in all_geofences:
            print(f"Geofence en BD: {gf.name} | lat: {gf.center_lat} | lon: {gf.center_lon} | radio: {gf.radius_m}")
