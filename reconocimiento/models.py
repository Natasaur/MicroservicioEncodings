from django.db import models

class RutaImagen(models.Model):
    matricula = models.CharField(max_length=20, unique=True)
    ruta_imagen = models.CharField(max_length=255)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.matricula} - {self.ruta_imagen}"