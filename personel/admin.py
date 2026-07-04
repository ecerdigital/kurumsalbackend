from django.contrib import admin
from .models import Employee, PositionPermission # <--- Buraya ekledik

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'tenant', 'position', 'email')
    list_filter = ('tenant', 'position')

# Yeni modelimizi admine kaydediyoruz
@admin.register(PositionPermission)
class PositionPermissionAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'position_name', 'can_view_employees', 'can_add_employee', 'can_edit_employee', 'can_delete_employee', 'can_view_salary')
    list_filter = ('tenant',)