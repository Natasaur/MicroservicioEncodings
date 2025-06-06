from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('index/', views.index, name='index'),
    path('logout/', views.logout, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('asistencia/', views.asistencia, name='asistencia'),
]