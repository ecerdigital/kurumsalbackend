from rest_framework import serializers
from .models import Employee, PositionPermission

class PositionPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PositionPermission
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'position', 'hire_date', 'salary', 'tenant_name']