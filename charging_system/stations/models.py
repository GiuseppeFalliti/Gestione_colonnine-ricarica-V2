from email import message
from django.db import models
from django.utils import timezone # timezone è un modulo di django che fornisce funzionalità per gestire le date e le ore 
import json


class Stazione_ricarica(models.Model):
    # 4 tipi di stati possibili della stazione
    STATUS=[
        ('available', 'Disponibile'), # (1_valore è il valore salvato nel db, 2_valore è l'etichetta da mostrare all'utente)
        ('occupied', 'Occupata'),
        ('faulted', 'Guasta'),
        ('unavailable', 'Non disponibile'),
    ]
     
    station_id = models.CharField(max_length=50, unique=True) # PK
    name= models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS, default='available') 
    power_capacity = models.FloatField()  # kW
    is_online = models.BooleanField(default=False) # Boolean per verificare se la stazione è accesa/spenta (default false)
    ultimo_segnale = models.DateTimeField(null=True, blank=True) # Data/ora ultimo segnale ricevuto
    created_at = models.DateTimeField(auto_now_add=True) # Data/ora di creazione (impostata automaticamente alla creazione)
    updated_at = models.DateTimeField(auto_now=True) # Data/ora ultimo aggiornamento (aggiornata automaticamente ad ogni modifica)

    # Definiamo che il modello viene rappresentato come una stringa che contine il nome e l'id della stazione di ricarica
    def __str__(self):
        return f"{self.name} ({self.station_id})"


class Sessione_ricarica(models.Model):
    session_id = models.CharField(max_length=50, unique=True) # PK
    station= models.ForeignKey(Stazione_ricarica, on_delete=models.CASCADE) #FK
    user_id= models.CharField(max_length=50)
    start_time= models.DateTimeField() # l'ora di inizio di una sessione di ricarica
    end_time= models.DateTimeField(null=True, blank=True) #  l'ora in cui finisce una sessione di ricarica
    energy_consumed= models.FloatField(default=0.0) # kWh
    transaction_id = models.CharField(max_length=50, null=True, blank=True) # id del pagamento della sessione di ricarica es paypal_txn_ABC123XYZ

    def __str__(self):
        return f"Sessione: {self.session_id} - {self.station.name}"


class OCPP_Messaggio(models.Model):
    MESSAGGIO =[
        ('call', 'Call'),
        ('callresult', 'CallResult'),
        ('callerror', 'CallError'),
    ]

    station=models.ForeignKey(Stazione_ricarica, on_delete=models.CASCADE)
    message_type=models.CharField(max_length=50, choices=MESSAGGIO)
    action = models.CharField(max_length=50)
    message_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.station.station_id} - {self.timestamp}"


# modello per rappresentare un dispositivo SNMP (colonnina).
class SNMPDevice(models.Model):
    """Rappresenta un dispositivo SNMP (colonnina)."""
    station = models.OneToOneField(Stazione_ricarica, on_delete=models.CASCADE) #Relazione OneToOne con la tabella Stazione_ricarica ovvero ogni stazione ha un dispositivo SNMP
    ip_address = models.GenericIPAddressField() # Indirizzo IP del dispositivo SNMP
    snmp_port = models.IntegerField(default=161) # Porta SNMP
    community_string = models.CharField(max_length=50, default='public') # Stringa di autenticazione(password) default standard per accedere ai dati SNMP in sola lettura
    snmp_version = models.CharField(max_length=10, default='2c') # Versione SNMP
    is_reachable = models.BooleanField(default=False) # Indica se il dispositivo è raggiungibile
    last_poll = models.DateTimeField(null=True, blank=True) # Data/ora dell'ultima interrogazione->risposta
    
    def __str__(self):
        return f"SNMP {self.station.station_id} - {self.ip_address}"

# modello per rappresentare le metriche raccolte via SNMP delle colonnine di ricarica.
class SNMPMetric(models.Model):
    """Metriche raccolte via SNMP"""
    METRICS=[
        ('voltage', 'Tensione(V)'),
        ('current', 'Corrente(A)'),
        ('power', 'Potenza(W)'),
        ('energy', 'Energia(kWh)'),
        ('temperature', 'Temperatura (°C)'),
        ('status', 'Stato'),
        ('uptime', 'Uptime'),
        ('network_traffic', 'Traffico di rete'),
    ]
    device = models.ForeignKey(SNMPDevice, on_delete=models.CASCADE) #Relazione ForeignKey con la tabella SNMPDevice
    metric_type = models.CharField(max_length=50, choices=METRICS) #Tipo di metrica
    oid = models.CharField(max_length=100) # Identificatore univoco per ogni parametro SNMP Esempio: 1.3.6.1.4.1.2021.10.1.3.1
    value = models.FloatField() #Valore della metrica
    string_value=models.CharField(max_length=100, null=True, blank=True) #Valore della metrica in stringa per metriche come lo stato
    timestamp = models.DateTimeField(auto_now_add=True) #Data/ora di raccolta della metrica

    # Definiamo un indice per i campi device, metric_type e timestamp per migliorare le prestazioni delle query
    class Meta:
        indexes = [
            models.Index(fields=['device', 'metric_type', 'timestamp']),
        ]
    
    # Definiamo che il modello viene rappresentato come una stringa che contiene il nome e l'id della stazione di ricarica
    def __str__(self):
        return f"{self.device.station.station_id} - {self.metric_type}: {self.value}"

# Modello per rappresentare gli alert basati su soglie SNMP ovvero messaggi di avviso da parte del dispositivo SNMP
class SNMPAlert(models.Model):
    """Alerti basati su soglie SNMP"""
    SEVERITY_LEVELS=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]
    device = models.ForeignKey(SNMPDevice, on_delete=models.CASCADE) #Relazione ForeignKey con la tabella SNMPDevice
    metric_type = models.CharField(max_length=50, choices=SNMPMetric.METRICS) #Tipo di metrica
    severity=models.CharField(max_length=50, choices=SEVERITY_LEVELS) #Livello di gravità dell'alert
    threshold_value = models.FloatField() #Soglia per l'alert
    current_value=models.FloatField() #Valore attuale della metrica
    message=models.TextField() #Messaggio dell'alert
    is_solved=models.BooleanField(default=False) #Indica se l'alert è stato risolto
    created_at=models.DateTimeField(auto_now_add=True) #Data/ora di creazione dell'alert
    risolved_at=models.DateTimeField(null=True, blank=True) #Data/ora di risoluzione dell'alert

    # Definiamo che il modello viene rappresentato come una stringa che contiene il livello di gravità, l'id della stazione di ricarica e il messaggio dell'alert
    def __str__(self):
        return f"{self.severity.upper()} - {self.device.station.station_id}: {self.message}"



class SNMPPollingConfig(models.Model):
    """Configurazione per il polling SNMP"""
    name = models.CharField(max_length=100) # Nome della configurazione
    oid = models.CharField(max_length=100) # OID per la metrica SNMP
    metric_type = models.CharField(max_length=20) # Tipo di metrica
    polling_interval = models.IntegerField(default=60)  # secondi
    threshold_min = models.FloatField(null=True, blank=True) # soglia minima
    threshold_max = models.FloatField(null=True, blank=True) # soglia massima
    is_active = models.BooleanField(default=True) # Indica se la configurazione è attiva
    
    # Definiamo che il modello viene rappresentato come una stringa che contiene il nome e l'oid
    def __str__(self):
        return f"{self.name} - {self.oid}"




