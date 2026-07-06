from django.contrib import admin
from django.urls import path, include
# SimpleJWT kütüphanesinin token alma fonksiyonları:
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Giriş yaparken React'ın aradığı tam adres burası (Sende burası eksik veya farklı):
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Personel uygulamasının rotası (Rol ve Personel yönetimi):
    path('api/personel/', include('personel.urls')), 
    path('api/roles/', include('personel.urls')),

    path('api/', include('muhasebe.urls')),

    path('api/', include('planlama.urls')),

]
