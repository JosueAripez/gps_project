# tracker/management/commands/export_data.py
from django.core.management.base import BaseCommand
from tracker.models import Geofence, Location, Device
from django.utils import timezone
import json, os
from django.conf import settings

class Command(BaseCommand):
    help = 'Export geofences and locations to exports/ folder and registrar datos de prueba'

    def handle(self, *args, **options):
        export_dir = os.path.join(settings.BASE_DIR, 'exports')
        os.makedirs(export_dir, exist_ok=True)

        # --- REGISTRA DATOS DE RECORRIDO DE PRUEBA ---
        device, _ = Device.objects.get_or_create(identifier='ensenada01', defaults={'name': 'Ensenada Tracker'})
        recorrido = [
            (31.8667, -116.5997),  # Centro Ensenada
            (31.8650, -116.6000),  # Cerca del malecón
            (31.8640, -116.6015),  # Calle Primera
            (31.8630, -116.6025),  # Plaza Cívica
            (31.8620, -116.6040),  # Mercado Negro
            (31.8610, -116.6060),  # Playa Hermosa
        ]
        now = timezone.now()
        for i, (lat, lon) in enumerate(recorrido):
            Location.objects.create(
                device=device,
                latitude=lat,
                longitude=lon,
                timestamp=now.replace(hour=8+i, minute=0, second=0)
            )
        print(f"Recorrido de prueba registrado para dispositivo 'ensenada01'.")

        # --- EXPORTA DATOS COMO ANTES ---
        def serialize(obj):
            result = {}
            for k, v in obj.items():
                if isinstance(v, (list, tuple)):
                    result[k] = [serialize(x) if isinstance(x, dict) else x for x in v]
                elif hasattr(v, 'isoformat'):
                    result[k] = v.isoformat()
                else:
                    result[k] = v
            return result

        geofences = [serialize(g) for g in Geofence.objects.all().values()]
        locations = [serialize(l) for l in Location.objects.all().values()]

        with open(os.path.join(export_dir, 'geofences_export.json'), 'w', encoding='utf-8') as f:
            json.dump(geofences, f, ensure_ascii=False, indent=2)

        with open(os.path.join(export_dir, 'locations_export.json'), 'w', encoding='utf-8') as f:
            json.dump(locations, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Exported {len(geofences)} geofences and {len(locations)} locations to {export_dir}'))
