from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем только для авторизованных пользователей
        if request.user.is_authenticated:
            # Проверяем ключ сессии
            if not request.session.session_key:
                # Сессия недействительна
                logout(request)
                messages.warning(request, 'Сессия истекла или недействительна. Пожалуйста, войдите снова.')
                return redirect('login')
            
            # Проверяем, что пользователь соответствует сессии
            session_user_id = request.session.get('_auth_user_id')
            if session_user_id and str(request.user.id) != session_user_id:
                # Обнаружено несоответствие пользователя и сессии
                logout(request)
                messages.warning(request, 'Обнаружена смена пользователя. Пожалуйста, войдите снова.')
                return redirect('login')
        
        response = self.get_response(request)
        return response