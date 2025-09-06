from django.db import models
from django.utils import timezone
import json

class Tracker(models.Model):
    """
    Rappresenta un localizzatore (tracker) montato su un veicolo.
    TABELLA: Tracker
    """
    Tracker_id= models.BigAutoField(primary_key=True)  # PK
    imei = models.CharField(max_length=20, db_index=True)
    plate_number = models.CharField("plate_number", max_length=20, blank=True, null=True, db_column="plate_number")
    status = models.CharField(max_length=32, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True, db_column="last seen")
    vin = models.CharField(max_length=17, blank=True, null=True)

    # Campi interi presenti nella tabella (tenuti come tali: non FK perché lo schema non li indica come tali)
    station_id = models.IntegerField(blank=True, null=True)
    tracker_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "Tracker"
        indexes = [
            models.Index(fields=["imei"]),
            models.Index(fields=["last_seen"]),
            models.Index(fields=["station_id"]),
        ]

    def __str__(self) -> str:
        base = f"Tracker {self.imei}"
        if self.plate_number:
            base += f" - {self.plate_number}"
        return base


class TrackerData(models.Model):
    """
    Dati telematici trasmessi dal tracker.
    TABELLA: Tracker_data
    """
    tracker = models.ForeignKey(
        Tracker,
        on_delete=models.CASCADE,
        related_name="data",
        db_column="Tracker_id", 
    )

    ts = models.DateTimeField(help_text="Timestamp del dato (origine dispositivo)")
    priority = models.PositiveSmallIntegerField(blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    altitude = models.IntegerField(blank=True, null=True, help_text="Altitudine in metri")
    angle = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Angolo/direzione 0-359")
    satellites = models.PositiveSmallIntegerField(blank=True, null=True, db_column="datellites")
    speed = models.FloatField(blank=True, null=True, help_text="Velocità (km/h)")
    event_id = models.IntegerField(blank=True, null=True)
    properties_count = models.PositiveIntegerField(blank=True, null=True)
    io_elements = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    km = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, help_text="Chilometri totali")

    class Meta:
        db_table = "Tracker_data"
        indexes = [
            models.Index(fields=["tracker", "ts"]),
            models.Index(fields=["ts"]),
            models.Index(fields=["event_id"]),
        ]
        ordering = ["-ts"]

    def __str__(self) -> str:
        return f"Data #{self.id} - tracker {self.tracker_id} @ {self.ts}"




# modello del tracker
class TrackerTypes(models.Model):
    id= models.BigIntegerField(max_length=10, primary_key=True)  # PK
    model= models.TextField(null=True, blank=True) # modello del veicolo
    description= models.TextField(null=True, blank=True) # descrizione del veicolo

    def __str__(self):
        return f"Model: {self.model}"


# dati I/O(parametri) del tracker
class Tracker_DataMap(models.Model):
    id= models.BigAutoField(max_length=10,primary_key=True)  # PK
    avl= models.IntegerField()
    trackerTypes_id= models.ForeignKey(TrackerTypes, on_delete=models.CASCADE) # FK
    unita= models.FloatField()
    fattore_moltiplicativo= models.FloatField(max_length=10)

    def __str__(self):
        return f"ID: {self.id} - AVL: {self.avl} - TrackerType ID: {self.trackerTypes_id}"


