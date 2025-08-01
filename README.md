# Sistema di Gestione Colonnine di Ricarica
Un sistema completo per la gestione e il monitoraggio di stazioni di ricarica per veicoli elettrici, sviluppato con Django e compatibile con il protocollo OCPP (Open Charge Point Protocol). Include monitoraggio SNMP avanzato e automazione con Celery.

## Indice
- [Caratteristiche](#caratteristiche)
- [Architettura](#architettura)
- [Monitoraggio SNMP](#monitoraggio-snmp)
- [Task Celery](#task-celery)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Licenza](#licenza)

## Caratteristiche

### Funzionalità Principali
- **Gestione Stazioni**: Monitoraggio completo delle colonnine di ricarica
- **Tracking Sessioni**: Registrazione e gestione delle sessioni di ricarica
- **Protocollo OCPP**: Supporto per messaggi OCPP standard
- **Monitoraggio SNMP**: Sistema avanzato di monitoraggio dispositivi di rete
- **Task Automatici**: Automazione con Celery per operazioni periodiche
- **API REST**: Interfacce JSON per integrazione con sistemi esterni
- **Monitoraggio Real-time**: ultimo segnale e status delle stazioni
- **Dashboard Ready**: Endpoint ottimizzati per dashboard e applicazioni mobile
- **Logging Avanzato**: Sistema di logging completo per debug e monitoraggio

### Caratteristiche Tecniche
- **Framework**: Django 4.2+
- **Database**: PostgreSQL
- **API**: REST JSON
- **Protocollo**: OCPP compatibile
- **SNMP**: Monitoraggio dispositivi di rete
- **Task Queue**: Celery con Redis
- **Logging**: Sistema multi-handler (file + console)
- **Architettura**: Modulare e scalabile

## Architettura

```python
charging_system/
├── charging_system/          # Configurazione principale Django
│   ├── settings.py          # Impostazioni del progetto + Celery + Logging
│   ├── urls.py             # URL routing principale
│   ├── celery.py           # Configurazione Celery
│   └── wsgi.py             # WSGI configuration
├── stations/               # App principale per le stazioni
│   ├── models.py          # Modelli di dati (inclusi SNMP)
│   ├── views.py           # Logica delle API
│   ├── urls.py            # URL routing dell'app
│   ├── tasks.py           # Task Celery per automazione
│   ├── snmp_manager.py    # Gestione connessioni SNMP
│   ├── apps.py            # Configurazione app Django
│   ├── __init__.py        # Integrazione Celery-Django
│   └── admin.py           # Configurazione admin
└── manage.py              # Script di gestione Django
```

## Monitoraggio SNMP

Il sistema include un modulo avanzato per il monitoraggio SNMP dei dispositivi di rete:

### Funzionalità SNMP
- **Gestione Dispositivi**: Configurazione e monitoraggio dispositivi SNMP
- **Raccolta Metriche**: Polling automatico delle metriche di rete
- **Gestione Errori**: Retry automatico e logging degli errori
- **Storico Dati**: Conservazione delle metriche storiche

### Modelli SNMP
- `SNMPDevice`: Configurazione dispositivi (IP, community, OID)
- `SNMPMetric`: Metriche raccolte con timestamp
- Integrazione con modello `Stazione_ricarica`

## Task Celery

Sistema di automazione basato su Celery per operazioni periodiche:

### Task Disponibili

#### `poll_all_snmp_devices`
- **Scopo**: Polling periodico di tutti i dispositivi SNMP
- **Frequenza**: Configurabile (tipicamente ogni 5-15 minuti)
- **Funzione**: Raccolta automatica delle metriche di rete

#### `cleanup_old_metrics`
- **Scopo**: Pulizia automatica delle metriche vecchie
- **Frequenza**: Ogni 24 ore
- **Funzione**: Elimina metriche più vecchie di 7 giorni (configurabile)
- **Vantaggi**: Mantiene il database performante

### Configurazione Celery
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'      # Coda task
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Risultati
CELERY_TIMEZONE = 'UTC'
```

### Avvio Worker Celery
```bash
# Attivare ambiente virtuale
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows

# Avviare worker Celery
celery -A charging_system worker --loglevel=info

# Avviare scheduler (per task periodici)
celery -A charging_system beat --loglevel=info
```

## Sistema di Logging

Configurazione avanzata per monitoraggio e debug:

### Handler di Logging
- **File Handler**: Salva log in `snmp_monitoring.log`
- **Console Handler**: Output real-time nel terminale
- **Livello**: INFO (include WARNING, ERROR, CRITICAL)

### Logger Specifici
- `stations.snmp_manager`: Log operazioni SNMP
- `stations.tasks`: Log task Celery
- Logging completo per debug e produzione

### Esempio Log
```
[INFO] stations.tasks: Deleted 150 old SNMP metrics
[INFO] stations.snmp_manager: Polling device 192.168.1.100
[ERROR] stations.snmp_manager: SNMP timeout for device 192.168.1.101
```

## Installazione

### Prerequisiti
- Python 3.8+
- pip (Python package manager)
- Virtualenv (raccomandato)

### Setup del Progetto
1. **Clona il repository**
    ```bash
    git clone <repository-url>
    cd charging_system
    ```

2. **Crea ambiente virtuale**
    ```bash
    python -m venv charging_station_env
    # Windows
    charging_station_env\Scripts\activate
    # Linux/Mac
    source charging_station_env/bin/activate
    ```

3. **Installa dipendenze**
    ```bash
    pip install django==4.2.16
    pip install djangorestframework  # Se necessario per future estensioni
    pip install celery[redis]  # Per task Celery
    pip install redis  # Per coda task Redis
    ```

4. **Configura il database**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. **Crea superuser (opzionale)**
    ```bash
    python manage.py createsuperuser
    ```

6. **Avvia il server**
    ```bash
    python manage.py runserver
    ```

Il server sarà disponibile su `http://127.0.0.1:8000/`

## Configurazione

### Impostazioni Database
Il progetto è configurato per SQLite di default. Per ambienti di produzione, modifica `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'charging_system_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Configurazione Celery
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'      # Coda task
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # Risultati
CELERY_TIMEZONE = 'UTC'
```

### Configurazione Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'snmp_monitoring.log',
        },
    },
    'loggers': {
        'stations.snmp_manager': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'stations.tasks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```
## Licenza
Questo progetto è rilasciato sotto la licenza MIT.
