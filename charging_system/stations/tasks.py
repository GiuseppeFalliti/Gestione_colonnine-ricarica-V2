from celery import shared_task # importa le funzioni di celery per creare task
from django.utils import timezone
from .models import SNMPDevice, Stazione_ricarica 
from .snmp_manager import snmp_manager
import logging # importa le funzioni di logging per tracciare errori e debug

logger = logging.getLogger(__name__)

"""
@shared_task è una Decorator di Celery che rende queste funzioni delle task asincrone eseguibili dal worker Celery
"""

@shared_task
def poll_all_snmp_devices():
    """Task per il polling di tutti i dispositivi SNMP"""
    devices = SNMPDevice.objects.select_related('station').all() #ottiene tutti i dispositivi SNMP con la stazione associata
    
    successful_polls = 0 #conta i dispositivi che hanno avuto successo
    failed_polls = 0 #conta i dispositivi che hanno avuto fallimento
    
    # per ogni dispositivo esegue il polling
    for device in devices:
        try:
            success = snmp_manager.poll_device_metrics(device)
            if success:
                successful_polls += 1
                # Aggiorna stato colonnina
                device.station.is_online = True
                device.station.last_heartbeat = timezone.now()
                device.station.save()
            else:
                failed_polls += 1
                # Marca come offline dopo fallimenti
                device.station.is_online = False
                device.station.save()
                
        except Exception as e:
            logger.error(f"Error polling device {device.station.station_id}: {e}")
            failed_polls += 1
    
    logger.info(f"SNMP polling completed: {successful_polls} successful, {failed_polls} failed")
    return {
        'successful': successful_polls,
        'failed': failed_polls,
        'timestamp': timezone.now().isoformat()
    }

@shared_task
def poll_single_device(device_id):
    """Task per il polling di un singolo dispositivo"""
    try:
        device = SNMPDevice.objects.get(id=device_id)
        success = snmp_manager.poll_device_metrics(device) #esegue il polling del dispositivo
        return {
            'device_id': device_id,
            'station_id': device.station.station_id,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }
    except SNMPDevice.DoesNotExist:
        logger.error(f"SNMP Device {device_id} not found")
        return {'error': 'Device not found'}


@shared_task
def cleanup_old_metrics(days=7):
    """Pulizia metriche vecchie"""
    from datetime import timedelta # importa la classe timedelta per calcolare intervallo di tempo
    from .models import SNMPMetric 
    
    cutoff_date = timezone.now() - timedelta(days=days) # calcola la data vecchia
    deleted_count = SNMPMetric.objects.filter(timestamp__lt=cutoff_date).delete()[0] # elimina le metriche vecchie
    
    logger.info(f"Deleted {deleted_count} old SNMP metrics") # logga il numero di metriche eliminate
    return {'deleted_count': deleted_count} # restituisce il numero di metriche eliminate