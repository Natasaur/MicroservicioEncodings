import os
import cv2
import face_recognition
import numpy as np
import bcrypt
from .utils.jwt import crear_access_token
from datetime import datetime
from pymongo import MongoClient
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render
from .decorators import jwt_required
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
#from .models import RutaImagen

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
            return render(request, 'reconocimiento/login.html', {"mensaje": "Usuario no encontrado", "vista": "login"})

        if not bcrypt.checkpw(password.encode(), usuario["password"].encode()):
            return render(request, 'reconocimiento/login.html', {"mensaje": "Contraseña incorrecta", "vista": "login"})

        # Generar token y pasar a siguiente vista (por ahora solo mostrar)
        token = crear_access_token(usuario)

        return render(request, 'reconocimiento/index.html', {
            "mensaje": f"Bienvenido {usuario['nombre']}",
            "token": token  # puedes mostrarlo o usarlo en JS
        })

    return render(request, 'reconocimiento/login.html', {"vista": "login"})

def logout(request):
    request.session.flush()  # Limpia la sesión
    return redirect('login')  # Redirige al login

@csrf_exempt
@jwt_required
def registro(request):
    if request.method == 'POST':
        matricula = request.POST.get('matricula')
        nombre = request.POST.get('nombre')
        apellido_paterno = request.POST.get('apellido_paterno')
        apellido_materno = request.POST.get('apellido_materno')
        grupo = request.POST.get('grupo')
        ciclo = request.POST.get('ciclo')
        contacto = request.POST.get('contacto')
        imagen = request.FILES.get('imagen')

        if not all([matricula, nombre, apellido_paterno, apellido_materno, grupo, ciclo, contacto, imagen]):
            return _respuesta(request, "Faltan campos obligatorios", 400)

        # Validar rostro
        ruta_img = os.path.join(settings.MEDIA_ROOT, f"{matricula}.jpg")
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        with open(ruta_img, 'wb+') as f:
            for chunk in imagen.chunks():
                f.write(chunk)

        #ruta_relativa = os.path.relpath(ruta_img, settings.BASE_DIR)

        #RutaImagen.objects.update_or_create(
        #    matricula=matricula,
        #    defaults={'ruta_imagen': ruta_relativa}
        #    )


        # RECONOCIMIENTO FACIAL
        img = cv2.imread(ruta_img)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detectar ubicación del rostro
        ubicaciones = face_recognition.face_locations(rgb)

        if len(ubicaciones) == 0:
            return _respuesta(request, "No se detectó ningún rostro en la imagen.", 400)

        if len(ubicaciones) > 1:
            return _respuesta(request, "Se detectaron múltiples rostros. Sube una foto en la que solo tú aparezcas.", 400)

        # Recortar el rostro
        top, right, bottom, left = ubicaciones[0]
        cara_recortada = img[top:bottom, left:right]

        # Sobrescribir la imagen original con solo la cara
        cv2.imwrite(ruta_img, cara_recortada)

        # Codificar el rostro recortado
        rgb_cara = cv2.cvtColor(cara_recortada, cv2.COLOR_BGR2RGB)
        codificaciones = face_recognition.face_encodings(rgb_cara)

        if len(codificaciones) == 0:
            return _respuesta(request, "No se pudo codificar el rostro recortado.", 400)

        encoding = codificaciones[0].tolist()

        cliente = MongoClient(DB_CLIENT)
        db = cliente["UConfortAsist"]
        alumnos = db["alumnos"]
        grupos = db["grupos"]

        grupo_valido = grupos.find_one({ "grupo": grupo, "disponible": True })
        if not grupo_valido:
            return _respuesta(request, "Verifique su grupo", 400)

        if alumnos.find_one({"matricula": matricula}):
            return _respuesta(request, f"La matrícula {matricula} ya está registrada.", 400)

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
        return _respuesta(request, "Registro exitoso", 200)

    return render(request, 'reconocimiento/registro.html', {"vista": "registro"})

#@csrf_exempt
#@jwt_required
def asistencia(request):
    if request.method == 'POST':
        imagen = request.FILES['imagen']
        ruta = os.path.join(settings.MEDIA_ROOT, "asistencia_temp.jpg")

        with open(ruta, 'wb+') as f:
            for chunk in imagen.chunks():
                f.write(chunk)

        img = cv2.imread(ruta)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        codificaciones = face_recognition.face_encodings(rgb)

        if len(codificaciones) == 0:
            return HttpResponse("No se detectó ningún rostro en la imagen.", status=400)

        if len(codificaciones) > 1:
            return HttpResponse("Se detectaron múltiples rostros. Sube una foto en la que solo tú aparezcas.", status=400)

        encoding_nuevo = codificaciones[0]

        cliente = MongoClient(DB_CLIENT)
        db = cliente["UConfortAsist"]
        alumnos_raw = list(db["alumnos"].find({"encoding": {"$exists": True}}))

        codificados = []
        alumnos_filtrados = []

        for alumno in alumnos_raw:
            codificados.append(np.array(alumno["encoding"]))
            alumnos_filtrados.append(alumno)

        if codificados and any(face_recognition.compare_faces(codificados, encoding_nuevo)):
            distancias = face_recognition.face_distance(codificados, encoding_nuevo)
            index = distancias.tolist().index(min(distancias))
            alumno = alumnos_filtrados[index]

            db["asistencias"].insert_one({
                "matricula": alumno["matricula"],
                "grupo": alumno["grupo"],
                "ciclo_escolar": alumno["ciclo_escolar"],
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "tipo_asistencia": "normal"
            })

            return HttpResponse(f"Asistencia de {alumno['nombre']} {alumno['apellido_paterno']} registrada correctamente", status=200)
        else:
            return HttpResponse("Rostro no coincide con ningún alumno registrado", status=400)

    # Si es GET, renderiza solo una vez el HTML
    return render(request, 'reconocimiento/asistencia.html', {"vista": "asistencia"})


def _respuesta(request, mensaje, status=200):
    # Si viene de fetch (JS) o tiene token
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.headers.get("Authorization"):
        return HttpResponse(mensaje, status=status)
    return render(request, 'reconocimiento/registro.html', {"mensaje": mensaje, "vista": "registro"})