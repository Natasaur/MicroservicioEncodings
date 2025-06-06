import os
import cv2
import face_recognition
import numpy as np
import bcrypt
# from django.http import JsonResponse
from pymongo import MongoClient
from .utils.jwt import crear_access_token
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings
from django.shortcuts import render
from .decorators import jwt_required
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# IP_PERMITIDA = "189.217.95.250"
DB_CLIENT = "mongodb+srv://uconfortasist:Udl8Q0APE93vt3BB@cluster0.g6qne.mongodb.net/UConfortAsist?retryWrites=true&w=majority"

def index(request):
    return render(request, 'reconocimiento/index.html')

def login(request):
    if request.method == "POST":
        correo = request.POST.get("correo")
        password = request.POST.get("password")

        if not correo or not password:
            return render(request, 'reconocimiento/login.html', {"mensaje": "Correo y contraseña obligatorios"})

        cliente = MongoClient(DB_CLIENT)
        db = cliente["UConfortAsist"]
        usuarios = db["usuarios"]

        usuario = usuarios.find_one({"correo": correo})

        if not usuario:
            return render(request, 'reconocimiento/login.html', {"mensaje": "Usuario no encontrado"})

        if not bcrypt.checkpw(password.encode(), usuario["password"].encode()):
            return render(request, 'reconocimiento/login.html', {"mensaje": "Contraseña incorrecta"})

        # Generar token y pasar a siguiente vista (por ahora solo mostrar)
        token = crear_access_token(usuario)

        return render(request, 'reconocimiento/index.html', {
            "mensaje": f"Bienvenido {usuario['nombre']}",
            "token": token  # puedes mostrarlo o usarlo en JS
        })

    return render(request, 'reconocimiento/login.html')

def logout(request):
    request.session.flush()  # Limpia la sesión
    return redirect('login')  # Redirige al login

@csrf_exempt
@jwt_required
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
        cliente = MongoClient(DB_CLIENT)
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
    return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje, "vista": "registro"})

@csrf_exempt
@jwt_required
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
        cliente = MongoClient(DB_CLIENT)
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
            
         # Responder con texto si la petición viene de fetch (JSON o no acepta HTML)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.headers.get("Authorization"):
            return HttpResponse(mensaje, status=200 if "registrada correctamente" in mensaje else 400)

    return render(request, 'reconocimiento/asistencia.html', {"mensaje": mensaje, "vista": "asistencia"})