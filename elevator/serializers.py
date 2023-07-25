from rest_framework.serializers import ModelSerializer, SerializerMethodField
from elevator.models import Elevator, ElevatorSystem, ElevatorRequest
from rest_framework.exceptions import ValidationError, NotFound
from django.db.models import F, Min
from utils.elevator import Abs

class ElevatorListSerializer(ModelSerializer):
    """
    Serializer for listing elevators.
    """
    is_available = SerializerMethodField()

    class Meta:
        model = Elevator
        fields = ["id", "current_floor", "is_available"]
        read_only_fields = ["id", "elevator_system"]

    def get_is_available(self, instance) -> bool:
        """
        Method to check if an elevator is available.
        :param instance: Elevator instance
        :return: True if elevator is available, False otherwise
        """
        # Check if the status of the elevator is 'available'
        if instance.status == "available":
            return True
        return False


class ElevatorDetailSerializer(ElevatorListSerializer):
    """
    Serializer for elevator details.
    """
    class Meta:
        model = Elevator
        fields = "__all__"


class ElevatorSystemSerializer(ModelSerializer):
    """
    Serializer for elevator system.
    """
    elevators = ElevatorListSerializer(many=True)

    class Meta:
        model = ElevatorSystem
        fields = "__all__"

    def validate(self, data):
        """
        Method to validate the data for an elevator system.
        :param data: data to be validated
        :return: validated data
        """
        no_of_floors = data["no_of_floors"]
        data["elevators"] = self.initial_data["elevators"]

        # Check if no_of_floors is an integer
        if not isinstance(no_of_floors, int):
            raise ValidationError("no_of_floors must be an integer")
        
        # Check if current_floor of each elevator is less than or equal to no_of_floors
        try:
            for elevator in data["elevators"]:
                if elevator["current_floor"] > no_of_floors:
                    raise ValidationError(
                        "Current Floor cannot be initialised above than total number of floors"
                    )
        except KeyError:
            raise ValidationError("Must specify current floor field in elevator object")
        return super().validate(data)

    def create(self, validated_data):
        """
        Method to create an elevator system.
        :param validated_data: validated data for creating an elevator system
        :return: created elevator system instance
        """

        # Get elevators data and create an elevator system instance
        elevators_data = validated_data.pop("elevators")
        elevator_system = ElevatorSystem.objects.create(**validated_data)

        # Create elevators instances and bulk create them
        elevators = [
            Elevator(elevator_system=elevator_system, **data) for data in elevators_data
        ]
        Elevator.objects.bulk_create(elevators)
        return elevator_system


class ElevatorRequestSerializer(ModelSerializer):
    """
    Serializer for elevator requests.
    """
    class Meta:
        model = ElevatorRequest
        fields = "__all__"
        extra_kwargs = {
            "elevator": {"read_only": True, "required": False},
            "elevator_system": {"read_only": True, "required": False},
        }

    def validate(self, data):
        """
        Method to validate the data for an elevator request.
        :param data: data to be validated
        :return: validated data
        """
        # Check if from_floor and to_floor are the same
        if data["from_floor"] == data["to_floor"]:
            raise ValidationError("You are at the same floor")
        
        return super().validate(data)

    def create(self, validated_data):
        """
        Method to create an elevator request.
        :param validated_data: validated data for creating an elevator request
        :return: created elevator request instance
        """
        
        # Get elevator system id from context and check if it exists
        elevator_system_id = self.context["view"].kwargs.get("elevator_system_pk", None)
        if elevator_system_id is None:
            raise ValidationError("Please specify elevator system id in url parameter")
        
        try:
            elevator_system = ElevatorSystem.objects.get(id=elevator_system_id)
            validated_data["elevator_system"] = elevator_system
        except ElevatorSystem.DoesNotExist:
            raise NotFound("Elevator System of given pk doesn't exist") 

        # Get from_floor from validated_data and check if it exists
        from_floor = validated_data["from_floor"]
        to_floor = validated_data["to_floor"]
        if from_floor is None:
            raise ValidationError("You need to specify from_floor in request body")
        
        # Get the closest available elevator and the first pending elevator request
        closest_available_elevator = (
            Elevator.objects.filter(status="available")
            .annotate(distance=Min(Abs(F("current_floor") - from_floor)))
            .order_by("distance")
            .first()
        )
        
        pending_elevator_request = elevator_system.elevator_requests.filter(status="QUEUED").first()

        # If there are no pending elevator requests and there is an available elevator, fulfill the request
        if closest_available_elevator and pending_elevator_request is None:
            if closest_available_elevator.current_floor != from_floor:
                closest_available_elevator.current_floor = from_floor
            else:
                closest_available_elevator.destination_floor = to_floor
            closest_available_elevator.status = "busy"
            closest_available_elevator.door = "close"
            closest_available_elevator.save(update_fields=["destination_floor", "status", "door"])
        
        # Check if there is a pending elevator request and fulfill it
        elif closest_available_elevator and pending_elevator_request is not None:
            pending_elevator_request.status = "PROCESSING"
            pending_elevator_request.save(update_fields=["status"])
            if closest_available_elevator.current_floor != pending_elevator_request.from_floor:
                closest_available_elevator.current_floor = pending_elevator_request.from_floor
            else: 
                closest_available_elevator.destination_floor = pending_elevator_request.to_floor
            closest_available_elevator.status = "busy"
            closest_available_elevator.door = "close"
            closest_available_elevator.save(update_fields=["destination_floor", "status", "door"])

        return ElevatorRequest.objects.create(elevator = closest_available_elevator, **validated_data)