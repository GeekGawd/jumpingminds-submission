from django.contrib import admin
from elevator.models import Elevator, ElevatorSystem

# Register your models here.

admin.site.register(ElevatorSystem)
admin.site.register(Elevator)

