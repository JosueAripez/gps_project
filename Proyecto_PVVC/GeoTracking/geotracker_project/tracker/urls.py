# tracker/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceViewSet, GeofenceViewSet, AlertViewSet, LocationCreateView, LastLocationView,
    index, DeviceUpdateLocationView, DeviceTrackView, AlertConfigView
)

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'geofences', GeofenceViewSet)
router.register(r'alerts', AlertViewSet, basename='alerts')

urlpatterns = [
    path('', index, name='index'),
    path('api/', include(router.urls)),
    path('api/locations/', LocationCreateView.as_view(), name='locations-create'),
    path('api/locations/last/', LastLocationView.as_view(), name='locations-last'),
    path('api/device/update_location/', DeviceUpdateLocationView.as_view(), name='device-update-location'),
    path('api/device/track/', DeviceTrackView.as_view(), name='device-track'),
    path('api/alert-config/', AlertConfigView.as_view(), name='alert-config'),
]
