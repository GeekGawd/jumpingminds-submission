from django.db import models
import uuid
from django.core.exceptions import ValidationError

# Create your models here.


class Elevator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_floor = models.IntegerField()
    is_operational = models.BooleanField(default=True)
    direction = models.CharField(max_length=255, choices=[(1, "up"), (2, "down")])

class ElevatorSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    elevators = models.ForeignKey(
        Elevator, related_name="elevator_system", on_delete=models.CASCADE
    )
    no_of_floors = models.IntegerField()
