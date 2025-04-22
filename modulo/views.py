from django.shortcuts import render,redirect,get_object_or_404
import requests
from .models import Libro, Categoria,HistorialBusqueda, LibroFavorito, LibroVisto, Reseña
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate,login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import random
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Redirigir al admin si es superusuario o staff
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
            
            return redirect('index')  # Redirige al index si es usuario normal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'modulo/login.html')

from django.contrib import messages

def index(request):
    libros_destacados = []
    query = request.GET.get('q', '')
    resultados = []

    # Obtener libros guardados por el usuario
    libros_guardados = []
    if request.user.is_authenticated:
        libros_guardados = set(
            f"{libro['titulo']}|{libro['autor']}"
            for libro in LibroFavorito.objects.filter(usuario=request.user).values('titulo', 'autor')
        )

    # Obtener libros sugeridos aleatoriamente desde la API de Google Books
    url_sugeridos = 'https://www.googleapis.com/books/v1/volumes?q=bestsellers'
    response_sugeridos = requests.get(url_sugeridos)
    if response_sugeridos.status_code == 200:
        data_sugeridos = response_sugeridos.json()
        libros = data_sugeridos.get('items', [])
        libros_destacados = [
            {
                'titulo': libro.get('volumeInfo', {}).get('title', 'Sin título'),
                'autores': libro.get('volumeInfo', {}).get('authors', ['Desconocido']),  # Lista de autores
                'portada': libro.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail', None),
                'link': libro.get('volumeInfo', {}).get('previewLink', '#')
            }
            for libro in libros[:4]  # Limitar a 4 libros sugeridos
        ]

    if query:
        if request.user.is_authenticated:
            HistorialBusqueda.objects.create(usuario=request.user, termino=query)

        # Usar la API de Google Books para buscar libros
        url = f'https://www.googleapis.com/books/v1/volumes?q={query}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                info = item.get('volumeInfo', {})
                resultados.append({
                    'titulo': info.get('title', 'Sin título'),
                    'autores': info.get('authors', ['Desconocido']),  # Lista de autores
                    'descripcion': info.get('description', 'Sin descripción'),
                    'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                    'link': info.get('previewLink', '#')  # Enlace a la vista previa
                })

    if not request.user.is_authenticated and len(resultados) > 3:
        resultados = resultados[:3]

    return render(request, 'modulo/index.html', {
        'libros_destacados': libros_destacados,
        'resultados': resultados,
        'query': query,
        'libros_guardados': libros_guardados
    })

def ver_libro(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor')  # Obtener el autor del formulario
        link = request.POST.get('link')
        portada = request.POST.get('portada')
        usuario = request.user

        # Validar que todos los campos necesarios estén presentes
        if not autor:
            autor = "Autor desconocido"  # Valor predeterminado si no se proporciona el autor

        # Crear el registro en la base de datos
        LibroVisto.objects.create(
            usuario=usuario,
            titulo=titulo,
            autor=autor,
            link=link,
            portada=portada
        )

        # Redirigir al enlace del libro
        return redirect(link)

    return redirect('index')  # Redirigir a la página principal si no es un POST


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario registrado con éxito. Ahora puedes iniciar sesión.')
            return redirect('login')  # asegúrate de que exista esta vista
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = UserCreationForm()

    return render(request, 'modulo/registro.html', {'form': form})

@require_POST
@login_required
def guardar_libro(request):
    titulo = request.POST.get('titulo')
    autor = request.POST.get('autor')
    link = request.POST.get('link')
    portada_url = request.POST.get('portada')

    # Crear el libro en la base si no existe
    libro, creado = Libro.objects.get_or_create(
        titulo=titulo,
        autor=autor,
        defaults={
            'link': link,
            'categoria': Categoria.objects.get_or_create(nombre='Importado')[0]
        }
    )

    if creado and portada_url:
        try:
            response = requests.get(portada_url)
            if response.status_code == 200:
                nombre_imagen = f"{libro.titulo.replace(' ', '_')}.jpg"
                libro.portada.save(nombre_imagen, ContentFile(response.content), save=True)
        except:
            pass  # Si no se puede descargar la portada, continuar sin error

    # Verificar si el libro ya está en favoritos
    ya_guardado = LibroFavorito.objects.filter(
        usuario=request.user,
        titulo=titulo,
        autor=autor
    ).exists()

    if not ya_guardado:
        LibroFavorito.objects.create(
            usuario=request.user,
            titulo=titulo,
            autor=autor,
            link=link,
            portada=portada_url
        )
        messages.success(request, 'Libro guardado exitosamente.')
    else:
        messages.info(request, 'Este libro ya estaba en tus favoritos.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def perfil(request):
    historial = HistorialBusqueda.objects.filter(usuario=request.user).order_by('-fecha')
    favoritos = LibroFavorito.objects.filter(usuario=request.user).order_by('-guardado_en')

    return render(request, 'modulo/perfil.html', {
        'historial': historial,
        'favoritos': favoritos
    })

@login_required
def marcar_libro_visto(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor')
        link = request.POST.get('link')
        portada = request.POST.get('portada')


        if not LibroVisto.objects.filter(usuario=request.user, titulo=titulo, autor=autor).exists():
            # Crear el registro solo si no existe
            LibroVisto.objects.create(
                usuario=request.user,
                titulo=titulo,
                autor=autor,
                link=link,
                portada=portada
            )
            messages.success(request, 'Libro marcado como visto.')
        else:
            messages.info(request, 'Este libro ya está marcado como visto.')

        return redirect(link)
    
@login_required
def detalle_libro(request, id):
    url = f'https://www.googleapis.com/books/v1/volumes/{id}'
    response = requests.get(url)
    libro = None
    libros_sugeridos = []

    if response.status_code == 200:
        data = response.json()
        info = data.get('volumeInfo', {})
        libro = {
            'titulo': info.get('title', 'Sin título'),
            'autor': ", ".join(info.get('authors', ['Desconocido'])),
            'portada': info.get('imageLinks', {}).get('thumbnail', ''),
            'descripcion': info.get('description', 'Sin descripción'),
            'link': info.get('previewLink', '#')  # Enlace a la vista previa
        }

    # Obtener libros sugeridos
    url_sugeridos = 'https://www.googleapis.com/books/v1/volumes?q=bestsellers'
    response_sugeridos = requests.get(url_sugeridos)
    if response_sugeridos.status_code == 200:
        data_sugeridos = response_sugeridos.json()
        for item in data_sugeridos.get('items', [])[:5]:  # Limitar a 5 libros sugeridos
            info = item.get('volumeInfo', {})
            libros_sugeridos.append({
                'titulo': info.get('title', 'Sin título'),
                'autor': ", ".join(info.get('authors', ['Desconocido'])),
                'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                'link': info.get('previewLink', '#')  # Enlace a la vista previa
            })

    return render(request, 'modulo/detalle_libro.html', {
        'libro': libro,
        'libros_sugeridos': libros_sugeridos,
        'id': id
    })

@login_required
def eliminar_libro_guardado(request, id):
    favorito = get_object_or_404(LibroFavorito, id=id, usuario=request.user)

    favorito.delete()
    messages.success(request, 'Libro eliminado de favoritos.')
    return redirect('perfil')
    
import requests


def autor_detalle(request, autor):
    # Si hay una coma, tomar solo el primer autor
    autor_principal = autor.split(',')[0].strip()

    # Usar la API de Wikipedia en español para obtener información del autor
    wikipedia_url = f"https://es.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": autor_principal,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
    }
    response = requests.get(wikipedia_url, params=params)
    autor_info = {
        "nombre": autor_principal,
        "biografia": "No se encontró información sobre este autor."
    }

    if response.status_code == 200:
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":  # Verificar que la página exista
                autor_info["biografia"] = page_data.get("extract", autor_info["biografia"])

    libros = []
    if request.user.is_authenticated:
        # Usar la API de Google Books para buscar libros del autor si el usuario está autenticado
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{autor_principal}"
        response_books = requests.get(google_books_url)

        if response_books.status_code == 200:
            data_books = response_books.json()
            for item in data_books.get('items', []):
                info = item.get('volumeInfo', {})
                libros.append({
                    'titulo': info.get('title', 'Sin título'),
                    'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                    'link': info.get('previewLink', '#')  # Enlace a la vista previa
                })

    return render(request, 'modulo/autor_detalle.html', {
        'autor': autor_info,
        'libros': libros,
        'mostrar_mensaje': not request.user.is_authenticated  
    })
