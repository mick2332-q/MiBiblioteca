from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from unidecode import unidecode
import re

# Create your models here.
# Modelo de Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre

# Modelo de Libro

def generate_slug(value):
    value = unidecode(value).lower().strip()
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value)
class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    ISBN = models.CharField(max_length=13, blank=True)
    fecha_publicacion = models.DateField(default='2000-01-01')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    portada = models.ImageField(upload_to='portadas/', blank=True, null=True)
    link = models.URLField(max_length=500, blank=True)
    creado_por_usuario = models.BooleanField(default=False)
    slug_titulo = models.SlugField(max_length=255, unique=False, blank=True)
    slug_autor = models.SlugField(max_length=255, unique=False, blank=True)
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True) # Añade descripción si no la tenías
    fecha_creacion_usuario = models.DateTimeField(auto_now_add=True, null=True, blank=True) # Para la fecha de creación por usuario

    def save(self, *args, **kwargs):
        if not self.slug_titulo:
            self.slug_titulo = generate_slug(self.titulo)
        if not self.slug_autor:
            self.slug_autor = generate_slug(self.autor)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

class HistorialBusqueda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    termino = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.termino}"

class LibroFavorito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True)
    portada = models.URLField(blank=True, null=True)
    guardado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'titulo', 'autor')

class LibroVisto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True)
    portada = models.URLField(blank=True, null=True)
    fecha_visto = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'titulo', 'autor')


class Reseña(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    libro_ISBN = models.CharField(max_length=13)
    texto = models.TextField()
    calificacion = models.IntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'libro_ISBN')

    def __str__(self):
        return f"Reseña de {self.usuario.username} para {self.libro_ISBN}"
    
class ComentarioExterno(models.Model):
    titulo = models.CharField(max_length=255)  
    autor = models.CharField(max_length=255)  
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.titulo}"

