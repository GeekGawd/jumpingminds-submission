from django.urls import path, include
from elevator import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

router = routers.SimpleRouter()

router.register(r"elevator-system", views.ElevatorSystemViewSet, basename="elevator-system")

elevator_system_nested_router = NestedSimpleRouter(router, r"elevator-system", lookup="elevator_system")
elevator_system_nested_router.register(r"elevators", views.ElevatorViewSet, basename="elevators")

# elevator_nested_router = NestedSimpleRouter(elevator_system_nested_router, r"elevators", lookup="elevator")
elevator_system_nested_router.register(r"elevator-request", views.ElevatorRequestViewSet, basename="elevator-requests")


# router.register(r"elevator-request", views.ElevatorRequestViewSet, basename="elevator-requests")

urlpatterns = [
    path("", views.HelloWorldAPI.as_view({"get": "list"}), name="hello-world"),
    path("", include(router.urls)),
    path("", include(elevator_system_nested_router.urls)),
    # path("", include(elevator_nested_router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="schema-docs"),
]
