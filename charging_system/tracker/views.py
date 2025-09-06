from django.shortcuts import render
from .models import Tracker  
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone
import json

# View per ottenere la lista di tutti i tracker
def tracker_list(request):
        if request.method != "GET":
            return JsonResponse({"errore"}, status=405)
        trackers = Tracker.objects.all()
        trackers_data = []

        now = timezone.now() 
        offline_status_time = now - timedelta(days=4) 

        for tracker in trackers:
            # controllo lo status in base a last_seen
            if tracker.last_seen <= offline_status_time:
                tracker.status = "offline"
            
            trackers_data.append({
                'Tracker_id': tracker.Tracker_id,
                'imei': tracker.imei,
                'plate_number': tracker.plate_number,
                'status': tracker.status,
                'last_seen': tracker.last_seen,
                'vin': tracker.vin,
                'station_id': tracker.station_id,
                'tracker_id': tracker.tracker_id,
            
            })
        return JsonResponse(trackers_data, safe=False)

# View per impostare o modificare o parametri di un tracker dato l'ID del tracker con metodo POST
def set_tracker(request, tracker_id):
    if request.method != "POST":
        return JsonResponse({"errore"}, status=405)
    
    tracker = Tracker.objects.get(Tracker_id=tracker_id) # ottengo il specifico tracker passato come parametro
    data = json.loads(request.body) # converte il corpo della richiesta JSON in un dizionario(array) Python
 
    # Aggiorna i campi del tracker se presenti nei dati della richiesta
    if 'plate_number' in data:
        tracker.plate_number = data['plate_number']
    if 'status' in data:
        tracker.status = data['status']
    if 'vin' in data:
        tracker.vin = data['vin']
    if 'station_id' in data:
        tracker.station_id = data['station_id']
    if 'tracker_id' in data:
        tracker.tracker_id = data['tracker_id']

    tracker.save()

    return JsonResponse({
        'Tracker_id': tracker.Tracker_id,
        'imei': tracker.imei,
        'plate_number': tracker.plate_number,
        'status': tracker.status,
        'last_seen': tracker.last_seen,
        'vin': tracker.vin,
        'station_id': tracker.station_id,
        'tracker_id': tracker.tracker_id,
    })

# View per ottenere i dettagli di un singolo tracker dato il suo ID
def get_tracker(request,tracker_id):
    if request.method != "GET":
        return JsonResponse({"errore"}, status=405)
    
    tracker= Tracker.objects.get(Tracker_id=tracker_id)
    return JsonResponse({
        'Tracker_id': tracker.Tracker_id,
        'imei': tracker.imei,
        'plate_number': tracker.plate_number,
        'status': tracker.status,
        'last_seen': tracker.last_seen,
        'vin': tracker.vin,
        'station_id': tracker.station_id,
        'tracker_id': tracker.tracker_id,
    })





