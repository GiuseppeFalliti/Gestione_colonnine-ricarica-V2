from django.urls import path
from . import views

urlpatterns = [
path('get_all_tracker/', views.tracker_list, name='get-tracker'),
path('set-tracker/<int:tracker_id>/', views.set_tracker, name='set-tracker'),
path('get-tracker/<int:tracker_id>/', views.get_tracker, name='get-tracker-id'),
]