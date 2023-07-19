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
from elevator.models import ElevatorSystem, Elevator
from rest_framework.decorators import action

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
        last_elevator_request = elevator.elevator_requests.last()

        if last_elevator_request.from_floor < last_elevator_request.to_floor:
            return Response({"status": "Elevator went up"})
        
        return Response({"status": "Elevator went down"})
    
    @action(methods=['get'], detail=True)
    def get_elevator_requests(self, request, *args, **kwargs):
        elevator_id = self.kwargs.get("pk", None)
        if elevator_id is None:
            raise ValidationError("You need to specify elevator id in query paramater")
        qs = Elevator.objects.get(id=elevator_id).elevator_requests.all()
        serializer = ElevatorRequestSerializer(qs, many=True)
        return Response(serializer.data)


class ElevatorRequestViewSet(GenericViewSet, CreateModelMixin):
    serializer_class = ElevatorRequestSerializer