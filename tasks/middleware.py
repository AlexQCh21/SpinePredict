# middleware.py
from django.conf import settings
from django.shortcuts import redirect
from datetime import datetime, timedelta

class AutoLogout:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            # Obtener el tiempo de la última actividad
            last_activity = request.session['last_activity']
            # Calcular el tiempo de expiración
            expire_time = settings.AUTO_LOGOUT_DELAY
            # Convertir last_activity a un objeto datetime
            last_activity_time = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - last_activity_time > timedelta(seconds=expire_time):
                # Cerrar la sesión si ha pasado el tiempo de inactividad permitido
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')
        except KeyError:
            pass

        # Actualizar la última actividad
        request.session['last_activity'] = str(datetime.now())

        return self.get_response(request)
    


from django.shortcuts import redirect
from django.urls import reverse

class RedirectAuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path == reverse('login'):
            return redirect('/') 
        return self.get_response(request)



from django.contrib.auth import authenticate
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages
from django.core.cache import cache  # Asegúrate de importar cache

class LoginAttemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/accounts/login/' and request.method == 'POST':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')  # Obtén la contraseña enviada
            key = f"login_attempts_{username}"
            max_attempts = 3

            # Recuperar datos de intentos desde la caché
            attempts_data = cache.get(key, {'attempts': 0, 'block_until': None})

            # Si el usuario está bloqueado
            if attempts_data['block_until'] and attempts_data['block_until'] > now():
                messages.error(request, 'Demasiados intentos fallidos. Intente nuevamente en 5 minutos.')
                return redirect('/accounts/login/')

            # Verificar credenciales del usuario
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Credenciales válidas, restablece el contador
                cache.delete(key)
            else:
                # Credenciales inválidas, incrementar intentos
                attempts_data['attempts'] += 1
                attempts_remaining = max(0, max_attempts - attempts_data['attempts'])

                if attempts_data['attempts'] >= max_attempts:
                    attempts_data['block_until'] = now() + timedelta(minutes=5)
                    messages.error(request, 'Se ha bloqueado el inicio de sesión por 5 minutos debido a múltiples intentos fallidos.')
                else:
                    messages.warning(
                        request,
                        f'Inicio de sesión fallido. Le quedan {attempts_remaining} intentos antes de ser bloqueado.'
                    )

                # Guardar los datos actualizados en la caché
                cache.set(key, attempts_data, timeout=300)

        return self.get_response(request)
