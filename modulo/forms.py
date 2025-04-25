from django import forms
from .models import Libro, UserProfile

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
    
class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['descripcion']  # SOLO descripcion

class EditarFotoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['foto_perfil']