from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary='Login via API',
        description='Autentica usuário e retorna cookie sessionid',
        responses={200: dict, 400: dict, 401: dict}
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username e password são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Forçar criação da sessão se não existir
            if not request.session.session_key:
                request.session.create()
            
            return Response({
                'status': 'logged_in',
                'username': user.username,
                'sessionid': request.session.session_key,
                'message': 'Use o valor de sessionid no cookieAuth do Swagger'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(APIView):
    @extend_schema(
        summary='Logout via API',
        description='Invalida sessão atual',
        responses={200: dict}
    )
    def post(self, request):
        logout(request)
        return Response({'status': 'logged_out'}, status=status.HTTP_200_OK)
