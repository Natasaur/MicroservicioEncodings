import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings
from django.shortcuts import render

IP_PERMITIDA = "189.217.95.250"

from django.shortcuts import render

def index(request):
    return render(request, 'reconocimiento/index.html')

def registro(request):
    mensaje = None
    if request.method == 'POST':
        matricula = request.POST['matricula']
        nombre = request.POST['nombre']
        apellido_paterno = request.POST['apellido_paterno']
        apellido_materno = request.POST['apellido_materno']
        grupo = request.POST['grupo']
        ciclo = request.POST['ciclo']
        contacto = request.POST['contacto']
        imagen = request.FILES['imagen']

        # Guardar imagen
        ruta_img = os.path.join(settings.MEDIA_ROOT, f"{matricula}.jpg")
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        with open(ruta_img, 'wb+') as f:
            for chunk in imagen.chunks():
                f.write(chunk)

        # Validar rostro
        img = cv2.imread(ruta_img)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        codificaciones = face_recognition.face_encodings(rgb)
        
        if len(codificaciones) == 0:
            mensaje = "No se detectó ningún rostro en la imagen."
            return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje})

        if len(codificaciones) > 1:
            mensaje = "Se detectaron múltiples rostros. Sube una foto en la que solo tú aparezcas."
            return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje})

            
        # Guardar alumno en MongoDB
        encoding = codificaciones[0].tolist()
        cliente = MongoClient("mongodb+srv://uconfortasist:Udl8Q0APE93vt3BB@cluster0.g6qne.mongodb.net/UConfortAsist?retryWrites=true&w=majority")
        db = cliente["UConfortAsist"]
        alumnos = db["alumnos"]
        grupos = db["grupos"]
        
        # Valida si el grupo existe y está disponible
        grupo_valido = grupos.find_one({ "grupo": grupo, "disponible": True })
        if not grupo_valido:
            mensaje = "Verifique su grupo"
            return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje})
        
        # Valida si la matricula ya esta registrada
        if alumnos.find_one({"matricula": matricula}):
            mensaje = f"La matricula {matricula} ya está registrada."
        else:            
            alumno = {
                "matricula": matricula,
                "nombre": nombre,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "grupo": grupo,
                "ciclo_escolar": ciclo,
                "contacto": contacto,
                "asistencias": [],
                "imagen": f"{matricula}.jpg",
                "encoding": encoding
            }
            alumnos.insert_one(alumno)
            mensaje = "Registro exitoso"
    return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje})


def asistencia(request):
    mensaje = None

    if request.method == 'POST':
        ip = request.META.get('REMOTE_ADDR')
        """if ip != |IP_PERMITIDA:
            return render(request, 'reconocimiento/asistencia.html', {
                "mensaje": "Solo puedes registrar asistencia desde la red de la escuela."
            })"""

        imagen = request.FILES['imagen']
        ruta = os.path.join(settings.MEDIA_ROOT, "asistencia_temp.jpg")

        with open(ruta, 'wb+') as f:
            for chunk in imagen.chunks():
                f.write(chunk)

        # Procesar imagen
        img = cv2.imread(ruta)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        codificaciones = face_recognition.face_encodings(rgb)

        if len(codificaciones) == 0:
            mensaje = "No se detectó ningún rostro en la imagen."
            return render(request, 'reconocimiento/asistencia.html', {"mensaje": mensaje})

        if len(codificaciones) > 1:
            mensaje = "Se detectaron múltiples rostros. Sube una foto en la que solo tú aparezcas."
            return render(request, 'reconocimiento/asistencia.html', {"mensaje": mensaje})
        
        encoding_nuevo = codificaciones[0]

        # Conectar con MongoDB y buscar coincidencia
        cliente = MongoClient("mongodb+srv://uconfortasist:Udl8Q0APE93vt3BB@cluster0.g6qne.mongodb.net/UConfortAsist?retryWrites=true&w=majority")
        db = cliente["UConfortAsist"]
        alumnos_raw = list(db["alumnos"].find({"encoding": {"$exists": True}}))
        
        codificados = []
        alumnos_filtrados = []
        
        for alumno in alumnos_raw:
            codificados.append(np.array(alumno["encoding"]))
            alumnos_filtrados.append(alumno)
        
        # Comparar rostros
        if codificados:
            resultados = face_recognition.compare_faces(codificados, encoding_nuevo)
            distancias = face_recognition.face_distance(codificados, encoding_nuevo)
        
        if any(resultados):
            index = distancias.tolist().index(min(distancias)) # el más parecido
            alumno = alumnos_filtrados[index]

            db["asistencias"].insert_one({
                "matricula": alumno["matricula"],
                "grupo": alumno["grupo"],
                "ciclo_escolar": alumno["ciclo_escolar"],
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "tipo_asistencia": "normal"
            })
            
            mensaje = f"Asistencia de {alumno['nombre']} {alumno['apellido_paterno']} registrada correctamente"
        else:
            mensaje = "Rostro no coincide con ningún alumno registrado"

    return render(request, 'reconocimiento/asistencia.html', {"mensaje": mensaje})