from django.contrib import admin
from elevator.models import Elevator, ElevatorSystem, ElevatorRequest

# Register your models here.

admin.site.register(ElevatorSystem)
admin.site.register(Elevator)
admin.site.register(ElevatorRequest)

