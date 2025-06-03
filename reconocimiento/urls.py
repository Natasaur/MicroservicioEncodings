from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='Inicio'),
    path('registro/', views.registro, name='registro'),
    path('asistencia/', views.asistencia, name='asistencia'),
] 