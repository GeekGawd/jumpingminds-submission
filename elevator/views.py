from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from elevator.serializers import (
    ElevatorSystemSerializer,
    ElevatorDetailSerializer,
    ElevatorRequestSerializer,
)
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from elevator.models import ElevatorSystem, Elevator, ElevatorRequest
from rest_framework.decorators import action
from django.db.models import F, Case, When, Max, Func, Min
from rest_framework import status

def service_elevator(elevator, time_increment = 0):
    if time_increment > 0:
        
        current_request = elevator.elevator_requests.filter(
            status='PROCESSING'
        ).last()
    
        # If no assigned request is found, continue
        if current_request is None:
            return time_increment

        # Calculate the direction and distance to the destination floor
        destination_floor = elevator.destination_floor or current_request.to_floor
        direction = 1 if destination_floor > elevator.current_floor else -1
        distance = abs(destination_floor - elevator.current_floor)

        # Move the elevator towards the destination floor
        floors_to_move = min(distance, time_increment)
        elevator.current_floor += direction * floors_to_move
        elevator.save(update_fields=["current_floor"])

        # If the elevator has reached the destination floor, update the request and elevator status
        if elevator.current_floor == destination_floor:
            if destination_floor == current_request.to_floor:
                elevator.status = 'available'
                elevator.destination_floor = None
                elevator.door = "open"
                elevator.save(update_fields=["status", "destination_floor", "door"])
                elevator.elevator_requests.filter(status="PROCESSING").update(status="FINISHED")
            else:
                elevator.destination_floor = current_request.to_floor
                elevator.save(update_fields=["destination_floor"])
        return min(distance, time_increment)
    return time_increment


def service_elevator_request(elevator_request):
    # Find closest available elevator request
    closest_available_elevator = (
            Elevator.objects.filter(status="available")
            .annotate(distance=Min(Abs(F("current_floor") - elevator_request.from_floor)))
            .order_by("distance")
            .first()
        )

    # If no available elevator is found, return None
    if closest_available_elevator is None:
        return None

    # Update the elevator status and destination floor
    closest_available_elevator.status = 'busy'
    closest_available_elevator.destination_floor = elevator_request.from_floor
    closest_available_elevator.save(update_fields=["status", "destination_floor"])

    # Update the elevator request status and associated elevator
    elevator_request.status = 'PROCESSING'
    elevator_request.elevator = closest_available_elevator
    elevator_request.save(update_fields=["status", "elevator"])

    return closest_available_elevator
    
class Abs(Func):
    function = "ABS"

class HelloWorldAPI(GenericViewSet):
    @extend_schema(responses={200: None})
    def list(self, request, *args, **kwargs):
        return Response({"status": "Hello World"})


class ElevatorSystemViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    queryset = ElevatorSystem.objects.all()
    serializer_class = ElevatorSystemSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class ElevatorViewSet(
    GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = ElevatorDetailSerializer

    def get_queryset(self):
        elevator_system_id = self.kwargs.get("elevator_system_pk", None)
        if elevator_system_id is None:
            raise ValidationError(
                "You need to specify elevator_system_id in query paramater"
            )
        return ElevatorSystem.objects.get(id=elevator_system_id).elevators.all()

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)
    
    @action(methods=['get'], detail=True)
    def get_direction(self, request, *args, **kwargs):
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        elevator = Elevator.objects.get(id=elevator_id)

        current_request = elevator.elevator_requests.filter(
            status='PROCESSING'
        ).last()
        if current_request is None:
            return Response({"status": "Elevator is idle, not moving"})
        
        destination_floor = elevator.destination_floor or current_request.to_floor
        direction = 1 if destination_floor > elevator.current_floor else -1

        if direction == 1:
            return Response({"status": "Elevator is going up"})
        
        return Response({"status": "Elevator is going down"})
    
    @action(methods=['get'], detail=True)
    def get_elevator_requests(self, request, *args, **kwargs):
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        qs = Elevator.objects.get(id=elevator_id).elevator_requests.all()
        serializer = ElevatorRequestSerializer(qs, many=True)
        return Response(serializer.data)
    
    @action(methods=['get'], detail=True)
    def get_next_destination_floor(self, request, *args, **kwargs):
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        elevator = Elevator.objects.get(id=elevator_id)

        # Find the current assigned request for the elevator
        current_request = ElevatorRequest.objects.filter(
            status='PROCESSING',
            elevator=elevator
        ).first()

        current_request = elevator.elevator_requests.filter(
            status='PROCESSING'
        ).last()
        if current_request is None:
            return Response({"status": "Elevator is idle, not moving"})
        
        destination_floor = elevator.destination_floor or current_request.to_floor

        return Response({"status": f"Next Destination Floor is {destination_floor}"})


class ElevatorRequestViewSet(GenericViewSet, CreateModelMixin):
    serializer_class = ElevatorRequestSerializer

class TimeIncrementViewSet(GenericViewSet):

    def get(self, request, *args, **kwargs):
        time_increment = 1

        # Increment the time_elapsed field in all ElevatorSystem objects
        ElevatorSystem.objects.update(time_elapsed=F('time_elapsed') + time_increment)

        # Service pending elevator requests and current assigned requests in all elevator systems
        for elevator_system in ElevatorSystem.objects.all():
            # Find all busy elevators in the current elevator system
            busy_elevators = Elevator.objects.filter(
                status='busy',
                elevator_system=elevator_system
            )

            # Service the current assigned request for each busy elevator
            for elevator in busy_elevators:

                # Check if there are any other pending requests that can be serviced by this elevator
                remaining_time = time_increment - service_elevator(elevator, time_increment)
                while remaining_time > 0:
                    # Find the next pending request that can be serviced by this elevator
                    next_request = ElevatorRequest.objects.filter(
                        status='QUEUED',
                        from_floor=elevator.current_floor,
                        elevator_system=elevator_system
                    ).first()

                    # If no such request is found, break out of the loop
                    if next_request is None:
                        break

                    # Update the next request status and associated elevator
                    next_request.status = 'PROCESSING'
                    next_request.elevator = elevator
                    next_request.save()

                    # Service the next request
                    remaining_time -= service_elevator(elevator, remaining_time)

            # Find all pending elevator requests in the current elevator system
            pending_requests = ElevatorRequest.objects.filter(
                status='QUEUED',
                elevator_system=elevator_system
            )

            # Service each pending request
            for elevator_request in pending_requests:
                # Find an available elevator to service the request
                available_elevator = service_elevator_request(elevator_request)

                # If no available elevator is found, continue to the next request
                if available_elevator is None:
                    continue

                # Service the current assigned request for the available elevator
                service_elevator(available_elevator, time_increment)
                

        return Response({"status": "Elevator System time successfully incremented"})