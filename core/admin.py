from django.contrib import admin
from .models import Tenant, CustomUser

admin.site.register(Tenant)

admin.site.register(CustomUser)