from functools import wraps
from django.http import JsonResponse
import jwt
from django.conf import settings

def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Permitir acceso GET sin token (solo proteger POST)
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'msg': 'Token no proporcionado o inválido'}, status=401)

        token = auth_header.split(' ')[1]
        print("Token recibido: ", token)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            request.user_payload = payload  # por si quieres usarlo dentro de la vista
        except jwt.ExpiredSignatureError:
            return JsonResponse({'msg': 'Token expirado'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'msg': 'Token inválido'}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper