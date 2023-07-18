from django.urls import path
from elevator import views
from rest_framework import routers

app_name = "elevator"

router = routers.SimpleRouter()

router.register("elevator-system", views.ElevatorSystemAPI, basename="elevator-system")
router.register("elevator", views.ElevatorAPI, basename="elevator")

urlpatterns = [
    path("", views.HelloWorldAPI.as_view({"get": "list"}), name="hello-world")
]
