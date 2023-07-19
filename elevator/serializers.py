from rest_framework.serializers import ModelSerializer, SerializerMethodField
from elevator.models import Elevator, ElevatorSystem, ElevatorRequest
from rest_framework.exceptions import ValidationError
from django.db.models import F, Min, Func

class Abs(Func):
    function = "ABS"

class ElevatorListSerializer(ModelSerializer):
    is_operational = SerializerMethodField()
    class Meta:
        model = Elevator
        fields = ["id", "current_floor", "is_operational"]
        read_only_fields = ['id', 'elevator_system']
    
    def get_is_operational(self, instance):
        if instance.status == "maintenance":
            return False
        return True

    
class ElevatorDetailSerializer(ElevatorListSerializer):
    class Meta:
        model = Elevator
        fields = "__all__"

class ElevatorSystemSerializer(ModelSerializer):
    elevators = ElevatorListSerializer(many=True)

    class Meta:
        model = ElevatorSystem
        fields = "__all__"

    def validate(self, data):
        no_of_floors = data["no_of_floors"]
        data["elevators"] = self.initial_data["elevators"]
        if not isinstance(no_of_floors, int):
            raise ValidationError("no_of_floors must be an integer")
        try:
            for elevator in data["elevators"]:
                if elevator["current_floor"] > no_of_floors:
                    raise ValidationError("Current Floor cannot be initialised above than total number of floors")
        except KeyError:
            raise ValidationError("Must specify current floor field in elevator object")
        return super().validate(data)

    def create(self, validated_data):
        elevators_data = validated_data.pop("elevators")
        elevator_system = ElevatorSystem.objects.create(**validated_data)
        elevators = [Elevator(elevator_system=elevator_system, **data) for data in elevators_data]
        Elevator.objects.bulk_create(elevators)
        return elevator_system

class ElevatorRequestSerializer(ModelSerializer):
    class Meta:
        model = ElevatorRequest
        fields = "__all__"
        extra_kwargs = {"elevator": {"read_only": True, "required": False}}
    
    def validate(self, data):
        if data["from_floor"] == data["to_floor"]:
            raise ValidationError("You are at the same floor")
        return super().validate(data)
    
    def create(self, validated_data):
        from_floor = validated_data["from_floor"]
        to_floor = validated_data["to_floor"]
        if from_floor is None:
            raise ValidationError("You need to specify from_floor in request body")
        closest_elevator = (
            Elevator.objects.exclude(status="maintenance").annotate(
                distance=Min(Abs(F("current_floor") - from_floor))
            )
            .order_by("distance")
            .first()
        )
        if closest_elevator is None:
            raise ValidationError("No Elevator is available")
        closest_elevator.current_floor = to_floor
        closest_elevator.save(update_fields=["current_floor"])
        return ElevatorRequest.objects.create(elevator=closest_elevator, **validated_data)