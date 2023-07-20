from typing import Collection, Iterable, Optional
from django.db import models
import uuid
from django.core.validators import MinValueValidator
from django.utils.functional import cached_property

# Create your models here.


def maximum_time_elapsed():
    """
    Function to calculate the maximum time elapsed for an elevator system.
    :return: maximum time elapsed or 0 if no elevator system exists
    """
    # Get the maximum time elapsed from the ElevatorSystem model
    maximum_time = ElevatorSystem.objects.aggregate(models.Max("time_elapsed"))[
        "time_elapsed__max"
    ]
    # If maximum time is None, return 0
    if maximum_time is None:
        return 0
    # Return the maximum time elapsed
    return maximum_time


class ElevatorSystem(models.Model):
    """
    Model to represent an elevator system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    time_elapsed = models.PositiveBigIntegerField(default=maximum_time_elapsed)
    no_of_floors = models.IntegerField()


class Elevator(models.Model):
    """
    Model to represent an elevator.
    """
    STATUS_CHOICES = [
        ("available", "Available"),
        ("busy", "Busy"),
        ("maintenance", "Maintenance"),
    ]
    DOOR_CHOICES = [
        ("open", "Open"),
        ("close", "Close"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )
    current_floor = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    destination_floor = models.IntegerField(
        default=None, validators=[MinValueValidator(1)], blank=True, null=True
    )
    elevator_system = models.ForeignKey(
        ElevatorSystem, related_name="elevators", on_delete=models.CASCADE
    )
    door = models.CharField(max_length=10, choices=DOOR_CHOICES, default="open")

    def __str__(self) -> str:
        return f"{self.id}--{self.status}"


class ElevatorRequest(models.Model):
    """
    Model to represent a request for an elevator.
    """
    STATUS = [
        ("FINISHED", "FINISHED"),
        ("QUEUED", "QUEUED"),
        ("PROCESSING", "PROCESSING"),
    ]
    elevator = models.ForeignKey(
        Elevator,
        related_name="elevator_requests",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    elevator_system = models.ForeignKey(
        ElevatorSystem, related_name="elevator_requests", on_delete=models.CASCADE
    )
    from_floor = models.IntegerField(validators=[MinValueValidator(1)])
    to_floor = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(choices=STATUS, max_length=15, default="QUEUED")

    def save(self, *args, **kwargs) -> None:
        if self.elevator is not None:
            self.status = "PROCESSING"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.id}--{self.status}"
