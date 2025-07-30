"""
questo file serve a trasformare una directory in un package Python. 
Quando Python vede questo file in una cartella, la tratta come un modulo importabile.
Le task in tasks.py non verrebbero riconosciute da Celery se nn ci fosse questo file
"""
from charging_system.celery import app as celery_app # import app di celery

__all__ = ('celery_app',) # esportazione l'app di celery