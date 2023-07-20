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
    ElevatorListSerializer
)
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from elevator.models import ElevatorSystem, Elevator, ElevatorRequest
from rest_framework.decorators import action
from django.db.models import F
from utils.elevator import elevator_service

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
    """
    ViewSet for elevator systems.
    """
    queryset = ElevatorSystem.objects.all()
    serializer_class = ElevatorSystemSerializer

    def create(self, request, *args, **kwargs):
        """
        Method to create an elevator system.
        """
        return super().create(request, *args, **kwargs)

class ElevatorViewSet(
    GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    """
    ViewSet for elevators.
    """
    serializer_class = ElevatorDetailSerializer

    def get_queryset(self):
        """
        Method to get the queryset for elevators.
        :return: Queryset for elevators
        """

        # Get elevator system id from context and check if it exists
        elevator_system_id = self.kwargs.get("elevator_system_pk", None)
        if elevator_system_id is None:
            raise ValidationError(
                "You need to specify elevator_system_id in query paramater"
            )
        
        # Return the elevators for the specified elevator system
        return ElevatorSystem.objects.get(id=elevator_system_id).elevators.all()

    def get_serializer(self, *args, **kwargs):

        # Return ElevatorListSerializer if action is 'list'
        if self.action == "list":
            return ElevatorListSerializer
        return super().get_serializer(*args, **kwargs)
    
    @action(methods=['get'], detail=True)
    def get_direction(self, request, *args, **kwargs):
        """
        Method to get the direction of an elevator.
        :param request: Request object
        :param args: Additional arguments
        :param kwargs: Additional keyword arguments
        :return: Response object with the direction of the elevator
        """

        # Get elevator id from context and check if it exists
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        
        # Get the specified elevator instance and its current request
        elevator = Elevator.objects.get(id=elevator_id)

        current_request = elevator.elevator_requests.filter(
            status='PROCESSING'
        ).last()
        if current_request is None:
            return Response({"status": "Elevator is idle, not moving"})
        
        # Mark the direction 1 for up and -1 for down
        destination_floor = elevator.destination_floor or current_request.to_floor
        direction = 1 if destination_floor > elevator.current_floor else -1

        if direction == 1:
            return Response({"status": "Elevator is going up"})
        
        return Response({"status": "Elevator is going down"})
    
    @action(methods=['get'], detail=True)
    def get_elevator_requests(self, request, *args, **kwargs):
        """
        Method to get the elevator requests for an elevator.
        :param request: Request object
        :param args: Additional arguments
        :param kwargs: Additional keyword arguments
        :return: Response object with the elevator requests for the specified elevator
        """
        
        # Get elevator id from context and check if it exists
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        
        # Get the specified elevator instance and its requests
        qs = Elevator.objects.get(id=elevator_id).elevator_requests.all()
        
        # Serialize the requests and return the response
        serializer = ElevatorRequestSerializer(qs, many=True)
        return Response(serializer.data)
    
    @action(methods=['get'], detail=True)
    def get_next_destination_floor(self, request, *args, **kwargs):
        """
        Method to get the next destination floor for an elevator.
        :param request: Request object
        :param args: Additional arguments
        :param kwargs: Additional keyword arguments
        :return: Response object with the next destination floor for the specified elevator
        """
        
        # Get elevator id from context and check if it exists
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        
        # Get the specified elevator instance and its current request
        elevator = Elevator.objects.get(id=elevator_id)
        
        current_request = ElevatorRequest.objects.filter(
            status='PROCESSING',
            elevator=elevator
        ).first()

        current_request = elevator.elevator_requests.filter(
            status='PROCESSING'
        ).last()
        
        # If no assigned request is found, return that the elevator is idle
        if current_request is None:
            return Response({"status": "Elevator is idle, not moving"})
        
        # Calculate the destination floor and return it in the response
        destination_floor = elevator.destination_floor or current_request.to_floor

        return Response({"status": f"Next Destination Floor is {destination_floor}"})


class ElevatorRequestViewSet(GenericViewSet, CreateModelMixin):
    """
    ViewSet for elevator requests.
    """
    serializer_class = ElevatorRequestSerializer

class TimeIncrementViewSet(GenericViewSet):

    def get(self, request, *args, **kwargs):
        """
        Method to increment time.
        :param request: Request object
        :param args: Additional arguments
        :param kwargs: Additional keyword arguments
        :return: Response object with a success message
        """
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
                remaining_time = time_increment - elevator_service.service_elevator(elevator, time_increment)
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
                    remaining_time -= elevator_service.service_elevator(elevator, remaining_time)

            # Find all pending elevator requests in the current elevator system
            pending_requests = ElevatorRequest.objects.filter(
                status='QUEUED',
                elevator_system=elevator_system
            )

            # Service each pending request
            for elevator_request in pending_requests:
                # Find an available elevator to service the request
                available_elevator = elevator_service.service_elevator_request(elevator_request)

                # If no available elevator is found, continue to the next request
                if available_elevator is None:
                    continue

                # Service the current assigned request for the available elevator
                elevator_service.service_elevator(available_elevator, time_increment)
                

        return Response({"status": "Elevator System time successfully incremented"})