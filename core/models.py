from django.db import models
from django.contrib.auth.models import AbstractUser

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    tax_no = models.CharField(max_length=11, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    
    ROLE_CHOICES = (
        ('admin', 'Şirket Yöneticisi'),
        ('manager', 'Müdür'),
        ('employee', 'Personel'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

    def __str__(self):
        return f"{self.username} ({self.tenant.name if self.tenant else 'Şirketsiz'})"