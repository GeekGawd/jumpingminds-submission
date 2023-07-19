from django.core.management.base import BaseCommand
from faker import Faker
from elevator.models import Elevator, ElevatorSystem
import random

class Command(BaseCommand):
    """Create fake data for Elevator and ElevatorSystem models"""
    help = "Create fake data for Elevator and ElevatorSystem models"
    def handle(self, *args, **options):
        fake = Faker()

        # Create fake data for Elevator model
        elevators = []
        for _ in range(10):
            elevator = Elevator(
                current_floor=random.randint(1, 10),
                is_operational=fake.boolean(),
                direction=random.choice([(1, "up"), (2, "down")])
            )
            elevators.append(elevator)
        Elevator.objects.bulk_create(elevators)

        # Create fake data for ElevatorSystem model
        elevator_systems = []
        for _ in range(5):
            elevator_system = ElevatorSystem(
                name=fake.word(),
                elevators=Elevator.objects.order_by('?').first(),
                no_of_floors=random.randint(5, 20)
            )
            elevator_systems.append(elevator_system)
        ElevatorSystem.objects.bulk_create(elevator_systems)

        print(self.style.SUCCESS('Successfully created fake data for Elevator and ElevatorSystem models'))
