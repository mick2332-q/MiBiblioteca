from django import forms
from .models import Libro, Categoria

class AgregarLibroUsuarioForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ['titulo', 'autor', 'link', 'portada', 'categoria'] # Añade 'categoria' aquí
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'required': False}),
            'portada': forms.FileInput(attrs={'class': 'form-control', 'required': False}),
            'categoria': forms.Select(attrs={'class': 'form-control'}), # Utiliza Select para un desplegable
        }