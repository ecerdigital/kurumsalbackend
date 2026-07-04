import string
import secrets
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import Employee, PositionPermission
from .serializers import EmployeeSerializer, PositionPermissionSerializer

User = get_user_model()

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sadece giriş yapan kullanıcının şirketine ait personelleri getirir
        return Employee.objects.filter(tenant=self.request.user.tenant)

    # ➕ PERSONEL EKLEME (POST /api/personel/) -> 400 Hatasını bitiren yer
    def create(self, request, *args, **kwargs):
        data = request.data
        tenant = request.user.tenant
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not email:
            return Response({"error": "E-posta alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        # Kullanıcı zaten var mı kontrolü
        if User.objects.filter(username=email).exists():
            return Response({"error": "Bu e-posta adresiyle zaten bir kullanıcı mevcut."}, status=status.HTTP_400_BAD_REQUEST)

        # 10 haneli şifre üretimi
        alphabet = string.ascii_letters + string.digits
        generated_password = ''.join(secrets.choice(alphabet) for _ in range(10))

        # 1. CustomUser Oluşturma
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

        # 2. Employee Kaydı (Hiçbir serializer validasyonuna takılmadan düz insert)
        employee = Employee.objects.create(
            tenant=tenant,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=data.get('phone', ''),
            position=data.get('position', ''),
            salary=data.get('salary', 0) or 0
        )

        # Terminale şifreyi yazdır
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

        # E-posta bildirim gönderme
        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=None,  # settings.py içindeki DEFAULT_FROM_EMAIL'i otomatik kullanır
                recipient_list=[email],
                fail_silently=False,  # Canlıda hatayı görebilmek için False yapıyoruz
            )
        except Exception as mail_error:
            # Eğer şifre veya port yanlışsa sunucu çökmez, terminale hatayı yazar
            print(f"❌ E-posta gönderilirken SMTP hatası oluştu: {mail_error}")

        # React'ın beklediği eklenen personel verisi
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)

    # ❌ PERSONEL SİLME (DELETE /api/personel/id/) -> 404 Hatasını bitiren yer
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Personelin bağlı olduğu bir CustomUser varsa onu da sistemden temizleyelim
            if instance.email:
                User.objects.filter(username=instance.email).delete()
                
            self.perform_destroy(instance)
            return Response({"message": "Personel ve bağlı kullanıcısı başarıyla silindi."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # 🔐 YETKİ KONTROLÜ (GET /api/personel/my-permissions/)
    @action(detail=False, methods=['get'], url_path='my-permissions')
    def my_permissions(self, request):
        user = request.user
        if user.is_superuser or getattr(user, 'is_staff', False):
            return Response({
                "position_name": "Sistem Yöneticisi", "can_view_employees": True, "can_add_employee": True,
                "can_edit_employee": True, "can_delete_employee": True, "can_view_salary": True
            })

        try:
            employee = Employee.objects.get(email=user.email, tenant=user.tenant)
            user_position = employee.position
            admin_keywords = ["müdür", "yönetici", "kurucu", "admin", "owner", "sahip", "ceo"]
            if any(keyword in user_position.lower() for keyword in admin_keywords):
                return Response({
                    "position_name": user_position, "can_view_employees": True, "can_add_employee": True,
                    "can_edit_employee": True, "can_delete_employee": True, "can_view_salary": True
                })
        except Employee.DoesNotExist:
            return Response({
                "position_name": "Şirket Kurucusu", "can_view_employees": True, "can_add_employee": True,
                "can_edit_employee": True, "can_delete_employee": True, "can_view_salary": True
            })

        try:
            permission = PositionPermission.objects.get(tenant=user.tenant, position_name=user_position)
            serializer = PositionPermissionSerializer(permission)
            return Response(serializer.data)
        except PositionPermission.DoesNotExist:
            return Response({
                "position_name": user_position, "can_view_employees": True, "can_add_employee": False,
                "can_edit_employee": False, "can_delete_employee": False, "can_view_salary": False
            })