from django.contrib import admin
from import_export.admin import ImportExportModelAdmin  # 👈 importa esto
from .models import Categoria, Libro,LibroFavorito, HistorialBusqueda

admin.site.register(LibroFavorito)
admin.site.register(HistorialBusqueda)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')

@admin.register(Libro)
class LibroAdmin(ImportExportModelAdmin):  # 👈 cambia aquí
    list_display = ('titulo', 'autor', 'categoria', 'fecha_publicacion')
    list_filter = ('categoria', 'fecha_publicacion')
    search_fields = ('titulo', 'autor')




