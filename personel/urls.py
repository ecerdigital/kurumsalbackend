from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'', EmployeeViewSet, basename='personel')
router.register(r'roles', RoleViewSet, basename='roles')

urlpatterns = [
    path('', include(router.urls)),
]
