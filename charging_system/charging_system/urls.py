from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('stations.urls')), # delego il lavoro al file urls dell app stations.
    path('tracker/', include('tracker.urls')), # delego il lavoro al file urls dell app tracker.
]