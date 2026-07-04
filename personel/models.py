from django.db import models
from core.models import Tenant # Core modülündeki Şirket yapısını çağırıyoruz

class Employee(models.Model):
    # MULTI-TENANCY: Bu personel hangi şirketin çalışanı?
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="employees")
    
    first_name = models.CharField(max_length=100, verbose_name="Adı")
    last_name = models.CharField(max_length=100, verbose_name="Soyadı")
    email = models.EmailField(unique=True, verbose_name="E-posta Adresi")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefonu")
    position = models.CharField(max_length=100, verbose_name="Pozisyonu / Görevi")
    hire_date = models.DateField(auto_now_add=True, verbose_name="İşe Giriş Tarihi")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maaşı")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.tenant.name})"

class PositionPermission(models.Model):
    # Her şirketin kendi pozisyon yetki haritası olmalı (Veri izolasyonu)
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, related_name='position_permissions')
    
    # Dashboard'daki POSITIONS listesiyle eşleşecek pozisyon adı (Örn: "Müdür", "Stajyer")
    position_name = models.CharField(max_length=100)
    
    # Yetki kutucukları (Açık/Kapalı - True/False)
    can_view_employees = models.BooleanField(default=True, verbose_name="Personelleri Görüntüleyebilir")
    can_add_employee = models.BooleanField(default=False, verbose_name="Personel Ekleyebilir")
    can_edit_employee = models.BooleanField(default=False, verbose_name="Personel Düzenleyebilir")
    can_delete_employee = models.BooleanField(default=False, verbose_name="Personel Silebilir")
    can_view_salary = models.BooleanField(default=False, verbose_name="Maaş Bilgisini Görebilir")

    class Meta:
        # Bir şirkette aynı pozisyon adından sadece bir tane yetki seti olabilir
        unique_together = ('tenant', 'position_name')

    def __str__(self):
        return f"{self.tenant.name} - {self.position_name} Yetkileri"