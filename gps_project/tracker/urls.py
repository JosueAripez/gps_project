from django.urls import path
from . import views

urlpatterns = [
    path("", views.map_view, name="map_view"),
    path("history/", views.history_view, name="history_view"),
    path("alerts_ui/", views.alerts_ui, name="alerts_ui"),
]
