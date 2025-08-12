import os
import cv2
import face_recognition

# Ruta a tu carpeta media (ajusta según tu entorno)
MEDIA_DIR = "/home/natasaur/facialweb_PA/media"

# Asegúrate de que sea una carpeta válida
if not os.path.isdir(MEDIA_DIR):
    print("La ruta especificada no existe.")
    exit()

procesadas = 0
omitidas = 0

for filename in os.listdir(MEDIA_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        ruta_img = os.path.join(MEDIA_DIR, filename)
        print(f"Procesando: {filename}")

        try:
            img = cv2.imread(ruta_img)
            if img is None:
                print(f"  ❌ No se pudo leer la imagen.")
                omitidas += 1
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            ubicaciones = face_recognition.face_locations(rgb)

            if len(ubicaciones) != 1:
                print(f"  ⚠️ {len(ubicaciones)} rostros detectados. Se omite.")
                omitidas += 1
                continue

            top, right, bottom, left = ubicaciones[0]
            cara_recortada = img[top:bottom, left:right]

            cv2.imwrite(ruta_img, cara_recortada)
            print("  ✅ Rostro recortado y guardado.")
            procesadas += 1

        except Exception as e:
            print(f"  ⚠️ Error al procesar {filename}: {e}")
            omitidas += 1

print(f"\nResumen:")
print(f"  ✅ Imágenes procesadas: {procesadas}")
print(f"  ⚠️ Imágenes omitidas: {omitidas}")
