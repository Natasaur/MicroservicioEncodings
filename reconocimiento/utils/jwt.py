import jwt
from django.conf import settings
from datetime import datetime, timedelta

def crear_access_token(usuario):
    exp = datetime.utcnow() + timedelta(hours=12)
    payload = {
        "matricula": usuario["matricula"],
        "rol": usuario["rol"],
        "exp": exp,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
