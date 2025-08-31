# Import specifici per pysnmp versione 7.x
# La versione 7.x ha una struttura di import diversa
from pysnmp.hlapi.v1arch.asyncio import *
from django.utils import timezone # importa le funzioni di gestione del tempo
import logging # importa le funzioni di logging per tracciare errori e debug
from .models import SNMPDevice, SNMPMetric, SNMPAlert, SNMPPollingConfig

# SNMP componenti principali:
# - SnmpEngine: Il motore che gestisce le comunicazioni
# - CommunityData: La "password" per accedere al dispositivo 
# - UdpTransportTarget: L'indirizzo IP e porta del dispositivo
# - ObjectIdentity: L'OID che identifica cosa vogliamo leggere

"""
1. get_snmp_value() → Singola richiesta SNMP
2. bulk_get_metrics() → Multiple richieste in batch
3. test_connectivity() → Verifica se il dispositivo risponde
4. poll_device_metrics() → Raccoglie tutte le metriche
5. _save_metrics() → Salva nel database
6. _check_thresholds() → Controlla alert
"""

logger = logging.getLogger(__name__)

class SNMPManager:
    """Gestisce le operazioni SNMP"""
    
    def __init__(self):
        self.timeout = 5 # Timeout di 5 secondi per le richieste
        self.retries = 3 # Numero di tentativi se fallisce
    

    def get_snmp_value(self, device, oid):
        """Ottiene un singolo valore SNMP"""
        try:
            # Configura la richiesta SNMP(Autenticazione)
            if device.snmp_version == '2c':
                auth_data = CommunityData(device.community_string) #CommunityData() metodo di pysnmp per autenticazione SNMP 
            else:
                # Per SNMP v3 (implementazione base)
                auth_data = CommunityData(device.community_string)
            
            # impostiamo IP e porta del dispositivo
            transport_target = UdpTransportTarget( 
                (device.ip_address, device.snmp_port),
                timeout=self.timeout,
                retries=self.retries
            )

            """
            nextCmd() è una funzione della libreria pysnmp che esegue la richiesta SNMP(stabilendo la comunicazione SNMP)
            per ogni iterazione del for restituisce una tupla contente errorIndication,
            errorStatus, errorIndex, varBinds(lista delle variabili SNMP restituite)
            """
            # Esecuzione richiesta GET SNMP
            iterator = getCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            errorIndication, errorStatus,varBinds = next(iterator)
            
            if errorIndication:
                logger.error(f"SNMP Error: {errorIndication}")
                return None
            
            if errorStatus:
                logger.error(f"SNMP Error: {errorStatus.prettyPrint()}")
                return None
                
            """
            se non ci sono errori restituisce il valore della variabile SNMP 
            varBind[1] contiene il valore della variabile SNMP
            varBind[0] contiene l'OID della variabile SNMP
            """
            for varBind in varBinds:
                return varBind[1].prettyPrint()
            
        except Exception as e:
            logger.error(f"SNMP Exception for {device.ip_address}: {e}")
            return None
    




    def bulk_get_metrics(self, device, oid_list):
        """Ottiene multiple metriche in una sola richiesta"""
        try:
            auth_data = CommunityData(device.community_string)
            transport_target = UdpTransportTarget(
                (device.ip_address, device.snmp_port),
                timeout=self.timeout,
                retries=self.retries
            )
            
            # lista di oggetti SNMP per ogni OID
            object_types = [] #lista di oggetti SNMP
            for oid in oid_list:
                object_types.append(ObjectType(ObjectIdentity(oid))) # ObjectType(ObjectIdentity(oid) trasforma l'OID in un oggetto SNMP
            
            results = {} # dizionario per memorizzare i risultati
            iterator = getCmd(
                SnmpEngine(),
                auth_data,
                transport_target,
                ContextData(),
                *object_types
            )
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication or errorStatus:
                return None
                
            for varBind in varBinds:
                oid = str(varBind[0])
                value = varBind[1].prettyPrint()
                results[oid] = value 
            
            return results # ES: {'1.3.6.1.2.1.1.1.0': 'System Description'}
            
        except Exception as e:
            logger.error(f"Bulk SNMP Exception for {device.ip_address}: {e}")
            return None
    



    def test_connectivity(self, device):
        """Testa la connettività SNMP"""
        # OID standard per system description
        system_desc_oid = '1.3.6.1.2.1.1.1.0'
        result = self.get_snmp_value(device, system_desc_oid)
        
        device.is_reachable = result is not None # se il dispositivo è raggiungibile
        device.last_poll = timezone.now() # Data/ora dell'ultima interrogazione->risposta
        device.save() # Salva le modifiche
        
        return device.is_reachable
    

    def poll_device_metrics(self, device):
        """Raccoglie tutte le metriche configurate per un dispositivo"""
        if not self.test_connectivity(device):
            logger.warning(f"Device {device.station.station_id} not reachable")
            return False
        
        # OID comuni per colonnine di ricarica (esempi)
        metric_oids = {
            '1.3.6.1.4.1.12345.1.1.1.0': 'voltage',      # Tensione
            '1.3.6.1.4.1.12345.1.1.2.0': 'current',      # Corrente
            '1.3.6.1.4.1.12345.1.1.3.0': 'power',        # Potenza
            '1.3.6.1.4.1.12345.1.1.4.0': 'energy',       # Energia
            '1.3.6.1.4.1.12345.1.1.5.0': 'temperature',  # Temperatura
            '1.3.6.1.2.1.1.3.0': 'uptime',               # Uptime sistema
        }
        
        # Raccogli metriche configurate
        configs = SNMPPollingConfig.objects.filter(is_active=True)
        oid_list = [config.oid for config in configs]

        
        if oid_list:
            results = self.bulk_get_metrics(device, oid_list)
            if results:
                self._save_metrics(device, results, configs)
        
        return True
    

    def _save_metrics(self, device, results, configs):
        """Salva le metriche nel database"""
        for config in configs:
            if config.oid in results:
                try:
                    value = float(results[config.oid])
                    
                    # Crea record metrica
                    metric = SNMPMetric.objects.create(
                        device=device,
                        metric_type=config.metric_type,
                        oid=config.oid,
                        value=value,
                        string_value=results[config.oid]
                    )
                    
                    # Controlla soglie e crea alert se necessario
                    self._check_thresholds(device, config, value)
                    
                except ValueError:
                    # Valore non numerico, salva come stringa
                    SNMPMetric.objects.create(
                        device=device,
                        metric_type=config.metric_type,
                        oid=config.oid,
                        value=0,
                        string_value=results[config.oid]
                    )
    


    def _check_thresholds(self, device, config, value):
        """Controlla le soglie e crea alert"""
        alert_needed = False
        severity = 'info'
        message = ''
        
        if config.threshold_max and value > config.threshold_max:
            alert_needed = True
            severity = 'critical'
            message = f"{config.metric_type} value {value} exceeds maximum threshold {config.threshold_max}"
        
        elif config.threshold_min and value < config.threshold_min:
            alert_needed = True
            severity = 'warning'
            message = f"{config.metric_type} value {value} below minimum threshold {config.threshold_min}"
        
        if alert_needed:
            # Verifica se esiste già un alert simile non risolto
            existing_alert = SNMPAlert.objects.filter(
                device=device,
                metric_type=config.metric_type,
                is_resolved=False
            ).first()
            
            if not existing_alert:
                SNMPAlert.objects.create(
                    device=device,
                    metric_type=config.metric_type,
                    severity=severity,
                    threshold_value=config.threshold_max or config.threshold_min,
                    current_value=value,
                    message=message
                )

# Istanza globale del manager
snmp_manager = SNMPManager()