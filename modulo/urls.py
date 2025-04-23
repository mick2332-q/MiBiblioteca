from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('perfil/', views.perfil, name='perfil'), 
    path('ver-libro/', views.marcar_libro_visto, name='ver_libro'),
    path('guardar-libro/', views.guardar_libro, name='guardar_libro'),
    path('agregar_comentario_externo/', views.agregar_comentario_externo, name='agregar_comentario_externo'),
    path('comentarios/<slug:titulo_slug>/<slug:autor_slug>/', views.comentarios_libro, name='comentarios_libro'),
    path('autor/<str:autor>/', views.autor_detalle, name='autor_detalle'),
    path('libro/<str:id>/', views.detalle_libro, name='detalle_libro'),
    path('eliminar-libro/<int:id>/', views.eliminar_libro_guardado, name='eliminar_libro'),
]