from django.urls import path
from .views import generar_encoding

urlpatterns = [
    path('api/encoding/', generar_encoding),
]