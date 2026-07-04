from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer

class RegisterView(APIView):
    # Bu API'a dışarıdan herkes (giriş yapmamış kişiler de) erişebilmeli
    permission_classes = [] 

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() # Serializer içindeki create fonksiyonunu tetikler
            return Response(
                {"status": "success", "message": "Şirket ve Yönetici kaydı başarıyla oluşturuldu!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)