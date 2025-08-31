from django.urls import path
from . import views

urlpatterns = [
    path('stations/', views.station_list, name='station_list'),
    path('stations/<str:station_id>/', views.station_detail, name='station_detail'),
    path('stations/<str:station_id>/status/', views.update_station_status, name='update_status'),

    path('snmp/devices/', views.snmp_devices_list, name='snmp_devices_list'),
    path('snmp/devices/<int:device_id>/', views.snmp_device_detail, name='snmp_device_detail'),
    path('snmp/devices/<int:device_id>/poll/', views.trigger_snmp_poll, name='trigger_snmp_poll'),
    path('snmp/devices/<int:device_id>/test/', views.snmp_test_connectivity, name='snmp_test_connectivity')
]