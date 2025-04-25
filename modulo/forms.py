from django import forms
from .models import Libro, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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


class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico")
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_password2(self):
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user