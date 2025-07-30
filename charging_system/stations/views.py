from django.shortcuts import render, get_object_or_404 # Funzioni di Django per renderizzare template e gestire oggetti non trovati
from django.http import JsonResponse #  Classe per restituire risposte JSON dalle view
from django.views.decorators.csrf import csrf_exempt # Decoratore per disabilitare la protezione CSRF
from django.utils import timezone # timezone è un modulo che gestisce le date e le ore 
from django.db.models import Avg, Max, Min, Count
from datetime import timedelta
import json 
from .models import Stazione_ricarica, Sessione_ricarica, OCPP_Messaggio, SNMPDevice, SNMPMetric, SNMPAlert
from .snmp_manager import snmp_manager
from .tasks import poll_single_device

# view function per ottenere la lista delle stazioni di ricarica.
def station_list(request):
    """Lista tutte le colonnine"""
    print("DEBUG: Iniziando station_list")  # Debug
    stations= Stazione_ricarica.objects.all() # variabile che contiene tutte le righe della tabella Stazione_ricarica (QuerySet)
    print(f"DEBUG: Trovate {stations.count()} colonnine")  # Debug
    stations_data = [] # lista inizialmente vuota

    for station in stations:
        print(f"DEBUG: Processando stazione {station.station_id}")  # Debug
        stations_data.append({
            'id': station.id,
            'station_id': station.station_id,
            'name': station.name,
            'status': station.status,
            'is_online': station.is_online,
            'ultimo_segnale': station.ultimo_segnale.isoformat() if station.ultimo_segnale else None
        })

    print(f"DEBUG: stations_data creato: {stations_data}")  # Debug
    return JsonResponse({'stations': stations_data}) # restituisce in formato JSON la lista delle stazioni



def station_detail(request,station_id):
    """Dettagli di una specifica colonnina"""
    station = get_object_or_404(Stazione_ricarica, station_id=station_id) # restituisce la stazione con il specifico id passato

    # Sessioni attive(cerca tutte le sessione di ricarica associata a quella determiata stazione)
    sessione_attiva= Sessione_ricarica.objects.filter(
        station=station,
        end_time__isnull=True #filtra solo le sessioni attive non ancora concluse
   )

    # Ultimi Messaggi OCPP
    recent_message= OCPP_Messaggio.objects.filter(
        station=station,
   ).order_by('-timestamp')[:10] # prende solo i primi 10 messaggi in ordine descrescente

    station_data={
    'station_id': station.station_id,
    'name': station.name,
    'power_capacity': station.power_capacity,
    'is_online': station.is_online,
    'status': len(station.status),
    'recent_messages': [
        {
          'action': msg.action,
          'timestamp': msg.timestamp.isoformat(),
          'data': msg.message_data
        } for msg in recent_message
    ]
    }

    return JsonResponse(station_data)

@csrf_exempt
def update_station_status(request, station_id):
    """Gestisce lo status di una colonnina (GET per leggere, POST per aggiornare)"""
    station = get_object_or_404(Stazione_ricarica, station_id=station_id)
    
    if request.method == 'GET':
        # Restituisce lo status attuale della stazione
        return JsonResponse({
            'status': station.status,
            'is_online': station.is_online,
            'ultimo_segnale': station.ultimo_segnale.isoformat() if station.ultimo_segnale else None
        })
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        
        # Aggiorna status
        if 'status' in data:
            station.status = data['status']
        
        # Aggiorna l'ultimo segnale
        station.ultimo_segnale = timezone.now()
        station.is_online = True
        station.save()
        
        # Salva messaggio OCPP
        OCPP_Messaggio.objects.create(
            station=station,
            message_type='call',
            action='StatusNotification',
            message_data=data
        )
        
        return JsonResponse({'success': True, 'message': 'Status updated'})
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    


# view function per ottenere la lista dei dispositivi SNMP
def snmp_devices_list(request):
    """Lista tutti i dispositivi SNMP"""
    devices = SNMPDevice.objects.select_related('station').all() #ottiene tutti i dispositivi SNMP che sono associati a una stazione di ricarica

    devices_data = []
    for device in devices:
        # Metriche recenti
        recent_metrics = SNMPMetric.objects.filter(
            device=device,
            timestamp__gte=timezone.now() - timedelta(days=7) #ottiene le metriche recenti
        ).order_by('-timestamp')[:10] #ottiene le 10 metriche più recenti

        # Alert attivi
        active_alerts = SNMPAlert.objects.filter(device=device, is_solved=False).count()

        #Aggiunge le informazioni del dispositivo alla lista
        devices_data.append({
            'id': device.id,
            'station_id': device.station.station_id,
            'ip_address': device.ip_address,
            'snmp_port': device.snmp_port,
            'community_string': device.community_string,
            'snmp_version': device.snmp_version,
            'is_reachable': device.is_reachable,
            'last_poll': device.last_poll.isoformat() if device.last_poll else None
        })

    return JsonResponse({'devices': devices_data}) #restituisce in formato JSON la lista dei dispositivi SNMP


def snmp_device_detail(request, device_id):
    """Dettagli dispositivo SNMP con metriche"""
    device = get_object_or_404(SNMPDevice, id=device_id) #ottiene il dispositivo SNMP con l'id passato 
    metrics = SNMPMetric.objects.filter(device=device).order_by('metric_type', 'timestamp') #ottiene tutte le metriche associate al dispositivo in ordine crescente per tipo e timestamp

    #organizzazione metriche per tipo
    metrics_by_type = {}
    for metric in metrics:
        if metric.metric_type not in metrics_by_type:
            metrics_by_type[metric.metric_type] = [] #inizializza una lista vuota per ogni tipo di metrica
        #Aggiunge la metrica alla lista del tipo corrispondente
        metrics_by_type[metric.metric_type].append({
            'value': metric.value,
            'timestamp': metric.timestamp.isoformat()
        })
    
    #Alert recenti
    alerts=SNMPAlert.objects.filter(device=device).order_by('-created_at')[:20]
    
    #riscriviamola con sintassi piu semplice
    alerts_data=[]
    for alert in alerts:
        alerts_data.append({
            'id': alert.id,
            'severity': alert.severity,
            'metric_type': alert.metric_type,
            'message': alert.message,
            'current_value': alert.current_value,
            'threshold_value': alert.threshold_value,
            'is_resolved': alert.is_resolved,
            'created_at': alert.created_at.isoformat(),
            'risolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
        })

    
    

    


    #Aggiunge le informazioni del dispositivo alla lista
    device_data={
        'id': device.id,
        'station_id': device.station.station_id,
        'ip_address': device.ip_address,
        'snmp_port': device.snmp_port,
        'community_string': device.community_string,
        'snmp_version': device.snmp_version,
        'is_reachable': device.is_reachable,
        'last_poll': device.last_poll.isoformat() if device.last_poll else None,
        'metrics': metrics_by_type
    }

    return JsonResponse(device_data)


@csrf_exempt
def start_snmp_poll(request, device_id):
    """Avvia polling manuale di un dispositivo"""
    if request.method == 'POST':
        device = get_object_or_404(SNMPDevice, id=device_id)
        
        # Avvia task asincrono
        task = poll_single_device(device_id)
        
        return JsonResponse({
            'success': True,
            'message': 'SNMP polling started',
            'task_id': task.id,
            'device_id': device_id
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def snmp_test_connectivity(request, device_id):
    """Testa connettività SNMP"""
    device = get_object_or_404(SNMPDevice, id=device_id)
    
    try:
        is_reachable = snmp_manager.test_connectivity(device)
        
        return JsonResponse({
            'device_id': device_id,
            'ip_address': device.ip_address,
            'is_reachable': is_reachable,
            'last_poll': device.last_poll.isoformat() if device.last_poll else None,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'device_id': device_id
        }, status=500)

@csrf_exempt
def trigger_snmp_poll(request, device_id):
    """Gestisce polling SNMP (GET per stato, POST per avviare)"""
    device = get_object_or_404(SNMPDevice, id=device_id)
    
    if request.method == 'GET':
        # Restituisce lo stato del dispositivo e info polling
        return JsonResponse({
            'device_id': device_id,
            'ip_address': device.ip_address,
            'is_reachable': device.is_reachable,
            'last_poll': device.last_poll.isoformat() if device.last_poll else None,
            'snmp_version': device.snmp_version,
            'community_string': device.community_string,
            'message': 'Use POST to trigger polling'
        })
    
    elif request.method == 'POST':
        # Avvia task asincrono
        task = poll_single_device.delay(device_id)
        
        return JsonResponse({
            'success': True,
            'message': 'SNMP polling started',
            'task_id': task.id,
            'device_id': device_id
        })
    
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)












