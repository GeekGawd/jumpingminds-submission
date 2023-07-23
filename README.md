# Jumping Minds Assignment - Elevator System
The document for the assignment is following, https://docs.google.com/document/d/1ZlJKfawiwqaEy2qoa0iAOB36Y0Ph5K2_zsvLcVJJBxk/edit

API’s required:
- Initialise the elevator system to create ‘n’ elevators in the system
- Fetch all requests for a given elevator
- Fetch the next destination floor for a given elevator
- Fetch if the elevator is moving up or down currently
- Saves user request to the list of requests for a elevator
- Mark a elevator as not working or in maintenance 
- Open/close the door.

The above APIs can be found at `/api/v1/schema/docs/` endpoint.

## Setup
### To Create Local Setup
1. Clone the repository:

```CMD
git clone https://github.com/anshumannandan/cryptBEE
```
To run the server, you need to have Python installed on your machine. If you don't have it installed, you can follow the instructions [here](https://www.geeksforgeeks.org/download-and-install-python-3-latest-version/) to install it.

2. Install & Create a virtual environment:

```CMD
pip install virtualenv
virtualenv venv
```

3. Activate the virtual environment:
```CMD
./venv/scripts/activate
```

4. Install the dependencies: 

```CMD
pip install -r requirements.txt
```

### Docker Setup

```CMD
docker-compose up --build -d
```

## Database Design

I used uuid field for Elevator System and Elevators because it is more safe than AutoIntegerField in Django, also I am specifying the ids in the url so it would not have been safe.

<p align="center">
  <img src="https://imgur.com/a/xrLeHz4" width="200" />  
</p>


### Elevator System
This model represents an elevator system that can be initialized with a certain number of elevators. It has fields for its id, name, time_elapsed, and no_of_floors.
I made this model, because I wanted the system to be flexible.

### Elevator
This model represents an individual elevator within an elevator system. It has fields for its id, status, current_floor, destination_floor, and associated elevator_system. It also has a door field to represent the state of its doors.

### Elevator Requests
This model represents a request made by a user to use an elevator to travel from one floor to another. It has fields for its associated elevator and elevator_system, as well as its from_floor and to_floor. It also has a status field to represent the state of the request.

## Logic

Going throught the documentation and tryin to implement the logic. I took the liberty to add a time factor to the elevator system. Because without it there would be no concept of busy state, given the elevators don't take any time to go up and down. So, I have made time_increment API, that increments the world by 1.

The elevators will automatically service requests using FIFO(First in First Out). If there are not service elevators available then they will be put in a Queue and will be serviced later on when the elevators become available.

## Video



## Notable Libraries Used

- DRF Nested Router - To easily reverse the url and support nesting in Django
- python-decouple - For environment variable
- Faker - To generate fake data
- drf-spectacular - To generate seagger documentation.

