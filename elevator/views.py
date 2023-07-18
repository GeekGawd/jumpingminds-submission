from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from elevator.serializers import ElevatorSystemSerializer, ElevatorSerializer


class HelloWorldAPI(GenericViewSet):
    def list(self, request, *args, **kwargs):
        return Response({"status": "Hello World"})


class ElevatorSystemAPI(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = ElevatorSystemSerializer
    
class ElevatorAPI(
    GenericViewSet,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = ElevatorSerializer
    
    def update(self, request, *args, **kwargs):
        request.data[""]
        if self.current_floor < 0:
            raise ValidationError("Elevator cannot be below ground floor")
        if self.direction == "up" and self.elevator_system.elevators:
            raise ValidationError("Elevator cannot go above 10th floor")
        return super().update(request, *args, **kwargs)
    
