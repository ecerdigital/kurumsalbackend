import string
import secrets
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import Employee, Role, Permission, EmployeeRole
from .serializers import EmployeeSerializer, RoleSerializer, PermissionSerializer, EmployeeRoleSerializer
from .permissions import HasPermission

User = get_user_model()

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Kullanıcının şirketine ait personelleri getir"""
        user = self.request.user
        tenant = getattr(user, 'tenant', None) or getattr(getattr(user, 'employee', None), 'tenant', None)
        
        if tenant:
            return Employee.objects.filter(tenant=tenant)
        return Employee.objects.all()
    
    def check_permission(self, permission_code):
        """Kullanıcının belirli izne sahip olup olmadığını kontrol et"""
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_staff', False):
            return True
        
        try:
            employee = Employee.objects.get(email=user.email, tenant=user.tenant)
            if hasattr(employee, 'role_assignment') and employee.role_assignment:
                return employee.role_assignment.has_permission(permission_code)
        except Employee.DoesNotExist:
            # Şirket kurucusu = Tüm izinler
            return True
        
        return False

    def list(self, request, *args, **kwargs):
        """Personel listesini görüntüle (personel_goruntule izni gerekli)"""
        if not self.check_permission('personel_goruntule'):
            return Response(
                {"error": "Bu işlem için yetkiniz yok. Personel listesini görüntüleme izni gereklidir."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Personel ekle (personel_ekle izni gerekli)"""
        if not self.check_permission('personel_ekle'):
            return Response(
                {"error": "Bu işlem için yetkiniz yok. Personel ekleme izni gereklidir."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        tenant = request.user.tenant
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not email:
            return Response({"error": "E-posta alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=email).exists():
            return Response({"error": "Bu e-posta adresiyle zaten bir kullanıcı mevcut."}, status=status.HTTP_400_BAD_REQUEST)

        # Şifre üretimi
        alphabet = string.ascii_letters + string.digits
        generated_password = ''.join(secrets.choice(alphabet) for _ in range(10))

        # CustomUser oluşturma
        user = User.objects.create_user(
            username=email,
            email=email,
            password=generated_password,
            first_name=first_name,
            last_name=last_name
        )
        if hasattr(user, 'tenant'):
            user.tenant = tenant
            user.save()

        # Employee kaydı
        employee = Employee.objects.create(
            tenant=tenant,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=data.get('phone', ''),
            position=data.get('position', ''),
            salary=data.get('salary', 0) or 0
        )

        # İsteğe bağlı olarak varsayılan bir rol atayabilir
        role_id = data.get('role_id')
        if role_id:
            try:
                role = Role.objects.get(id=role_id, tenant=tenant)
                EmployeeRole.objects.update_or_create(
                    employee=employee,
                    defaults={'role': role, 'assigned_by': request.user}
                )
            except Role.DoesNotExist:
                pass

        print("\n" + "="*50)
        print(f"🎉 PERSONEL BAŞARIYLA KAYDEDİLDİ!")
        print(f"Kullanıcı: {email}")
        print(f"Şifre: {generated_password}")
        print("="*50 + "\n")

        email_subject = f"🎉 {tenant.name} Yönetim Paneline Hoş Geldiniz!"
        email_message = f"""
Merhaba {first_name} {last_name},

{tenant.name} bünyesinde '{data.get('position', 'Personel')}' olarak sisteme kaydınız başarıyla gerçekleştirilmiştir.

Şirket yönetim paneline aşağıdaki bilgilerinizle giriş yapabilirsiniz:

🔗 Giriş Adresi: http://localhost:3000
📧 Kullanıcı Adı: {email}
🔑 Geçici Şifre: {generated_password}

Güvenliğiniz için sisteme ilk giriş yaptıktan sonra "Profil" sekmesinden şifrenizi değiştirmeniz önerilir.

Keyifli çalışmalar dileriz,
{tenant.name} İnsan Kaynakları Yönetimi
        """

        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as mail_error:
            print(f"❌ E-posta gönderilirken SMTP hatası oluştu: {mail_error}")

        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Personel sil (personel_sil izni gerekli)"""
        if not self.check_permission('personel_sil'):
            return Response(
                {"error": "Bu işlem için yetkiniz yok. Personel silme izni gereklidir."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = self.get_object()
            
            if instance.email:
                User.objects.filter(username=instance.email).delete()
                
            self.perform_destroy(instance)
            return Response({"message": "Personel ve bağlı kullanıcısı başarıyla silindi."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # 🔐 PERSONEL YETKİLERİNİ AL
    @action(detail=False, methods=['get'], url_path='my-permissions')
    def my_permissions(self, request):
        """Giriş yapan kişinin tüm izinlerini getir"""
        user = request.user
        
        if user.is_superuser or getattr(user, 'is_staff', False):
            return Response({
                "user_type": "Sistem Yöneticisi",
                "role": None,
                "permissions": [
                    'personel_ekle', 'personel_sil', 'personel_goruntule',
                    'muhasebe_goruntule', 'muhasebe_islem',
                    'planlama_goruntule', 'planlama_islem'
                ]
            })

        try:
            employee = Employee.objects.get(email=user.email, tenant=user.tenant)
            
            # Eğer personele rol atanmışsa
            if hasattr(employee, 'role_assignment') and employee.role_assignment and employee.role_assignment.role:
                role = employee.role_assignment.role
                permissions = [p.permission_code for p in role.permissions.all()]
                return Response({
                    "user_type": "Personel",
                    "role": RoleSerializer(role).data,
                    "permissions": permissions
                })
        except Employee.DoesNotExist:
            # Personel kaydı yok = Şirket kurucusu
            pass
        
        # Varsayılan: Şirket kurucusu (tüm izinler)
        return Response({
            "user_type": "Şirket Kurucusu",
            "role": None,
            "permissions": [
                'personel_ekle', 'personel_sil', 'personel_goruntule',
                'muhasebe_goruntule', 'muhasebe_islem',
                'planlama_goruntule', 'planlama_islem'
            ]
        })

    # 👤 PERSONELE ROL ATA
    @action(detail=True, methods=['post'], url_path='assign-role')
    def assign_role(self, request, pk=None):
        """Belirli bir personele rol ata"""
        if not self.check_permission('personel_ekle'):  # Benzer izin kontrol et
            return Response(
                {"error": "Bu işlem için yetkiniz yok."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        employee = self.get_object()
        role_id = request.data.get('role_id')
        
        if not role_id:
            return Response({"error": "role_id gereklidir."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = Role.objects.get(id=role_id, tenant=employee.tenant)
            employee_role, created = EmployeeRole.objects.update_or_create(
                employee=employee,
                defaults={'role': role, 'assigned_by': request.user}
            )
            
            message = "Rol başarıyla atanmıştır." if created else "Rol başarıyla güncellenmiştir."
            return Response({
                "message": message,
                "employee_role": EmployeeRoleSerializer(employee_role).data
            }, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({"error": "Rol bulunamadı."}, status=status.HTTP_404_NOT_FOUND)


class RoleViewSet(viewsets.ModelViewSet):
    """Rol yönetimi"""
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Kullanıcının şirketine ait rolleri getir"""
        user = self.request.user
        tenant = getattr(user, 'tenant', None) or getattr(getattr(user, 'employee', None), 'tenant', None)
        
        if tenant:
            return Role.objects.filter(tenant=tenant)
        return Role.objects.all()
    
    def perform_create(self, serializer):
        """Rol oluştururken tenant'ı otomatik ata"""
        tenant = self.request.user.tenant
        serializer.save(tenant=tenant)
