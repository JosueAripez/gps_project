from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/device/(?P<identifier>[^/]+)/$', consumers.DeviceConsumer.as_asgi()),
]
