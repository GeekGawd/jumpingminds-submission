from typing import Collection, Optional
from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.functional import cached_property

# Create your models here.

class ElevatorSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    time_elapsed = models.PositiveBigIntegerField(default=0)
    no_of_floors = models.IntegerField()

class Elevator(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('maintenance', 'Maintenance'),
    ]
    DOOR_CHOICES = [
        ('open', 'Open'),
        ('close', 'Close'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    current_floor = models.IntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ]
    )
    elevator_system = models.ForeignKey(ElevatorSystem, related_name="elevators", on_delete=models.CASCADE)
    door = models.CharField(max_length=10, choices=DOOR_CHOICES, default="open")

    @cached_property
    def is_operational(self):
        if self.status == "available":
            return True
        return False

class ElevatorRequest(models.Model):
    elevator = models.ForeignKey(Elevator, related_name="elevator_requests", on_delete=models.CASCADE)
    from_floor = models.IntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )
    to_floor = models.IntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    def __str__(self) -> str:
        return f"{self.id}--{self.elevator.id}"