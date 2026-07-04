from rest_framework import serializers
from .models import Tenant, CustomUser

class RegisterSerializer(serializers.Serializer):
    
    company_name = serializers.CharField(max_length=255)
    tax_no = serializers.CharField(max_length=11)
    
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_tax_no(self, value):
        if Tenant.objects.filter(tax_no=value).exists():
            raise serializers.ValidationError("Bu vergi numarası ile zaten bir şirket kayıtlı.")
        return value

    def create(self, validated_data):
        tenant = Tenant.objects.create(
            name=validated_data['company_name'],
            tax_no=validated_data['tax_no']
        )
        
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            tenant=tenant,
            role='admin'
        )
        return user