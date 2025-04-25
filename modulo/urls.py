from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('perfil/', views.perfil, name='perfil'), 
    path('ver-libro/', views.marcar_libro_visto, name='ver_libro'),
    path('guardar-libro/', views.guardar_libro, name='guardar_libro'),
    path('comentarios/<slug:titulo_slug>/<slug:autor_slug>/', views.comentarios_libro, name='comentarios_libro'),
    path('autor/<str:autor>/', views.autor_detalle, name='autor_detalle'),
    path('libro/<str:id>/', views.detalle_libro, name='detalle_libro'),
    path('eliminar-libro/<int:id>/', views.eliminar_libro_guardado, name='eliminar_libro'),
    path('editar_comentario/<int:comentario_id>/', views.editar_comentario, name='editar_comentario'),
    path('eliminar_comentario/<int:comentario_id>/', views.eliminar_comentario, name='eliminar_comentario'),
    path('libros-guardados/', views.libros_guardados, name='libros_guardados'),
    path('mis-libros/', views.libros_creados, name='libros_creados'),
    path('crear-libro/', views.crear_libro, name='crear_libro'),
    path('historial/', views.historial, name='historial_vistos'),
]