from django.shortcuts import render
from .models import Tracker, Tracker_DataMap, TrackerTypes
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
    
    if not Tracker_DataMap.objects.filter(id=tracker_id).exists():
        return JsonResponse({"errore": "Tracker non trovato"}, status=404)
    
    else:
        data = json.loads(request.body) # converte il corpo della richiesta JSON in un dizionario(array) Python
        """aggiorna il tracker con i nuovi dati: update(**data) aggiorna il record con i dati contenuti in data.
        l operatore ** è l operatore che spacchetta il dizionario in coppie chiave-valore.
        es: {'plate_number': 'ABC123', 'status': 'active'} diventa plate_number='ABC123', status='active'
          """
        Tracker_DataMap.objects.filter(id=tracker_id).update(**data) 
        return JsonResponse({
            "message": f"Tracker {tracker_id} aggiornato con successo",
            "data_received": data
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





