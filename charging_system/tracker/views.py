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

# View per aggiungere o modificare o parametri di un tracker dato l'ID del tracker con metodo POST
def set_tracker(request, trackerid):
    if request.method != "POST":
        return JsonResponse({"errore"}, status=405)
    
    data = json.loads(request.body) # converte il corpo della richiesta JSON in un dizionario(array) Python
    
    if not Tracker_DataMap.objects.filter(tracker_id=trackerid).exists():
        Tracker_DataMap.objects.create(**data) # crea un nuovo tracker con i dati ricevuti
        return JsonResponse({
            "message": f"Nuovo tracker {trackerid} creato con successo",
            "data_received": data
        }, status=201)
        
    
    else:
        """aggiorna il tracker con i nuovi dati: update(**data) aggiorna il record con i dati contenuti in data.
        l operatore ** è l operatore che spacchetta il dizionario in coppie chiave-valore.
        es: {'plate_number': 'ABC123', 'status': 'active'} diventa plate_number='ABC123', status='active'
          """
        Tracker_DataMap.objects.filter(tracker_id=trackerid).update(**data) 
        return JsonResponse({
            "message": f"Tracker {trackerid} aggiornato con successo",
            "data_received": data
        })

# View per modificare o aggiungere un tracker
def add_tracker(request):
    if request.method != "POST":
        return JsonResponse({"errore"}, status=405)
    
    data = json.loads(request.body)
    # crea un nuovo tracker con i dati ricevuti
    if Tracker.objects.filter(tracker_id=data['id']).exists():
        Tracker.objects.filter(tracker_id=data['id']).update(**data)
        return JsonResponse({
            "message": f"Tracker {data['id']} aggiornato con successo",
            "data_received": data
        }, status=200)

    else:    
        new_tracker = Tracker.objects.create(**data)

        return JsonResponse({
        "message": "Nuovo tracker creato con successo",
        "tracker_id": new_tracker.Tracker_id,
        "data_received": data
        }, status=201)


# View per ottenere i parametri di un singolo tracker dato il suo ID
def get_tracker(request,trackerid):
    if request.method != "GET":
        return JsonResponse({"errore"}, status=405)
    
    if not Tracker.objects.get(Tracker_id=trackerid):
        return JsonResponse({"errore": "Tracker non trovato"}, status=404)
    
    else:
        if Tracker_DataMap.objects.filter(tracker_id=trackerid).exists():
            return JsonResponse({
                'data': list(Tracker_DataMap.objects.filter(tracker_id=trackerid).values())

            })

#View per per eliminare uno o piü parametri di un tracker dato l'id di un tracker
def delete_tracker(request, trackerid):
    if request.method != "DELETE":
        return JsonResponse({"errore"}, status=405)
    
    if not Tracker_DataMap.objects.filter(id=trackerid).exists():
        return JsonResponse({"errore": "Tracker non trovato"}, status=404)
    
    else:
        data= json.loads(request.body)
        # elimina i parametri del tracker specificato nell'array data
        if 'id' in data:
            Tracker_DataMap.objects.filter(id=trackerid).delete()
        if 'avl' in data:
            Tracker_DataMap.objects.filter(avl=data['avl']).delete()
        if 'formula' in data:
            Tracker_DataMap.objects.filter(formula=data['formula']).delete()
        if 'unita' in data:
            Tracker_DataMap.objects.filter(unita=data['unita']).delete()
        if 'fattore_moltiplicativo' in data:
            Tracker_DataMap.objects.filter(fattore_moltiplicativo=data['fattore_moltiplicativo']).delete()
        
        return JsonResponse({
            "message": f"Parametri del tracker: {trackerid} eliminato con successo"
        })
    

#View per elimare un tracker
def delete_entire_tracker(request, trackerid):
    if request.method != "DELETE":
        return JsonResponse({"errore"}, status=405)
    
    if not Tracker.objects.filter(Tracker_id=trackerid).exists():
        return JsonResponse({"errore": "Tracker non trovato"}, status=404)
    
    else:
        Tracker.objects.filter(Tracker_id=trackerid).delete()
        return JsonResponse({
            "message": f"Tracker: {trackerid} eliminato con successo"
        })











