import os
import cv2
import face_recognition
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser])
def generar_encoding(request):
    
    print('FILES:', request.FILES)
    print('POST:', request.POST)

    
    imagen = request.FILES.get('imagen')
    if not imagen:
        return JsonResponse({'error': 'No se envió la imagen'}, status=400)

    # Guardar temporalmente la imagen
    ruta_img = os.path.join(settings.MEDIA_ROOT, "temp.jpg")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    with open(ruta_img, 'wb+') as f:
        for chunk in imagen.chunks():
            f.write(chunk)

    # Leer y convertir a RGB
    img = cv2.imread(ruta_img)
    if img is None:
        return JsonResponse({'error': 'Error al leer la imagen'}, status=400)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detectar rostros
    ubicaciones = face_recognition.face_locations(rgb)
    if len(ubicaciones) == 0:
        return JsonResponse({'error': 'No se detectó ningún rostro'}, status=400)
    if len(ubicaciones) > 1:
        return JsonResponse({'error': 'Se detectaron múltiples rostros'}, status=400)

    # Codificar rostro
    codificaciones = face_recognition.face_encodings(rgb, known_face_locations=ubicaciones)
    if not codificaciones:
        return JsonResponse({'error': 'No se pudo codificar el rostro'}, status=400)

    encoding = codificaciones[0].tolist()
    return JsonResponse({'encoding': encoding}, status=200)