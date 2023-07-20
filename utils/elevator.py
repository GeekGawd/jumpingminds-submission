from elevator.models import Elevator
from django.db.models import F, Min, Func

class Abs(Func):
    """
    Class to represent the absolute value function.
    """
    function = "ABS"


class ElevatorService:
    """
    Service class for elevators.
    """

    @staticmethod
    def service_elevator(elevator, time_increment=0):
        """
        Method to service an elevator.
        :param elevator: Elevator instance to be serviced
        :param time_increment: Time increment for servicing the elevator
        :return: Time increment after servicing the elevator
        """
        
        # Check if time_increment is greater than 0
        if time_increment > 0:
            
            # Get the current request for the elevator
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

    @staticmethod
    def service_elevator_request(elevator_request):
        """
        Method to service an elevator request.
        :param elevator_request: ElevatorRequest instance to be serviced
        :return: Closest available Elevator instance or None if no available elevators are found
        """
        
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


elevator_service = ElevatorService()