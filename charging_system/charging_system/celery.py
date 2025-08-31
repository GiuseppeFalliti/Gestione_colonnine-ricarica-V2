import os
from celery import Celery
from django.conf import settings

# Imposta il modulo delle impostazioni Django per Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'charging_system.settings') # Dice a Celery di usare le impostazioni Django

app = Celery('charging_system') # Crea un'istanza di Celery

# Configurazione da Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Scopri automaticamente i task nelle app Django
# metodo che permette a Celery di trovare e caricare il file tasks.py, e registra tutti i @shared_task
app.autodiscover_tasks() 

# Configurazione task periodici 
app.conf.beat_schedule = {
    'poll-snmp-devices': {
        'task': 'stations.tasks.poll_all_snmp_devices',
        'schedule': 60.0,  # ogni 60 secondi
    },
    'cleanup-old-metrics': {
        'task': 'stations.tasks.cleanup_old_metrics',
        'schedule': 24 * 60 * 60.0,  # ogni 24 ore
    },
}

app.conf.timezone = 'UTC'