from django.contrib import admin
from import_export.admin import ImportExportModelAdmin  
from .models import Categoria, Libro,LibroFavorito, HistorialBusqueda,ComentarioExterno

admin.site.register(LibroFavorito)
admin.site.register(HistorialBusqueda)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')

@admin.register(Libro)
class LibroAdmin(ImportExportModelAdmin):  
    list_display = ('titulo', 'autor', 'categoria', 'fecha_publicacion')
    list_filter = ('categoria', 'fecha_publicacion')
    search_fields = ('titulo', 'autor')

@admin.register(ComentarioExterno)
class ComentarioExternoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'usuario', 'fecha_creacion', 'contenido')
    list_filter = ('fecha_creacion', 'usuario', 'titulo', 'autor')
    search_fields = ('titulo', 'autor', 'contenido', 'usuario__username')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)



