from rest_framework.serializers import ModelSerializer
from elevator.models import Elevator, ElevatorSystem
from rest_framework.exceptions import ValidationError

class ElevatorSystemSerializer(ModelSerializer):
    class Meta:
        model = ElevatorSystem
        fields = "__all__"
    
    def validate(self, data):
        no_of_elevators = data["no_of_elevators"]
        if not isinstance(no_of_elevators, int):
            raise ValidationError("no_of_elevators must be an integer")
        return super().validate(data)
    
    def create(self, validated_data):
        self.validated_data = validated_data["no_of_elevators"]
        elevators_data = validated_data.pop("elevators") 
        elevators = [Elevator(**data) for data in elevators_data]
        Elevator.objects.bulk_create(elevators)
        return super().create(validated_data)
    
class ElevatorSerializer(ModelSerializer):
    class Meta:
        model = Elevator
        fields = "__all__"
