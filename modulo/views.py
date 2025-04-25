from django.shortcuts import render,redirect,get_object_or_404
import requests
from .models import Libro, Categoria,HistorialBusqueda, LibroFavorito, LibroVisto,ComentarioExterno,UserProfile
from .forms import AgregarLibroUsuarioForm,EditarPerfilForm,EditarFotoForm,RegistroUsuarioForm
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate,login,update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.text import slugify
from collections import defaultdict
from unidecode import unidecode
import re ,random
from django.utils import timezone
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
            
            
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
            
            return redirect('index')  
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'modulo/login.html')

from django.contrib import messages



def index(request):
    libros_destacados = []
    query = request.GET.get('q', '')
    resultados = []

    libros_guardados = []
    if request.user.is_authenticated:
        libros_guardados = set(
            f"{libro['titulo']}|{libro['autor']}"
            for libro in LibroFavorito.objects.filter(usuario=request.user).values('titulo', 'autor')
        )

    libros_reconocidos = [
        "Cien años de soledad",
        "Harry Potter y la piedra filosofal",
        "El amor en los tiempos del cólera",
        "El túnel",
    ]

    libros_aleatorios = random.sample(libros_reconocidos, 1)
    url_sugeridos = f'https://www.googleapis.com/books/v1/volumes?q={libros_aleatorios}'
    response_sugeridos = requests.get(url_sugeridos)
    if response_sugeridos.status_code == 200:
        data_sugeridos = response_sugeridos.json()
        libros = data_sugeridos.get('items', [])
        libros_destacados = [
            {
                'titulo': libro.get('volumeInfo', {}).get('title', 'Sin título').strip(),
                'autores': [autor.strip() for autor in libro.get('volumeInfo', {}).get('authors', ['Desconocido'])],
                'portada': libro.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail', None),
                'link': libro.get('volumeInfo', {}).get('previewLink', '#')
            }
            
            for libro in libros[:4]
        ]
    if query:
        if request.user.is_authenticated:
            HistorialBusqueda.objects.create(usuario=request.user, termino=query)

        
        url = f'https://www.googleapis.com/books/v1/volumes?q={query}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                info = item.get('volumeInfo', {})
                resultados.append({
                    'titulo': info.get('title', 'Sin título').strip(),
                    'autores': [autor.strip() for autor in info.get('authors', ['Desconocido'])],
                    'descripcion': info.get('description', 'Sin descripción'),
                    'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                    'link': info.get('previewLink', '#')
                })  
    from .models import Libro

    libros_usuario_publicos = Libro.objects.filter(creado_por_usuario=True).order_by('-fecha_publicacion')
    for libro_usuario in libros_usuario_publicos:
        
        resultados.append({
            'titulo': libro_usuario.titulo,
            'autores': [libro_usuario.autor],
            'descripcion': libro_usuario.descripcion if libro_usuario.descripcion else 'Sin descripción proporcionada por el usuario.',
            'portada': libro_usuario.portada.url if libro_usuario.portada else '',
            'link': libro_usuario.link if libro_usuario.link else '',
            'es_usuario': True, 
            'slug_titulo': libro_usuario.slug_titulo,
            'slug_autor': libro_usuario.slug_autor,
        })
    if not request.user.is_authenticated and len(resultados) > 3:
        resultados = resultados[:3]

    comentarios_por_libro = defaultdict(int)
    for comentario in ComentarioExterno.objects.all():
        
        titulo_norm = normalizar_datos(comentario.titulo)
        autor_norm = normalizar_datos(comentario.autor.split(',')[0])  
        key = f"{titulo_norm}|{autor_norm}"
        comentarios_por_libro[key] += 1

        
    for libro in resultados + libros_destacados:
        titulo_norm = normalizar_datos(libro.get('titulo', '') if isinstance(libro, dict) else libro.titulo)
        autor_norm = normalizar_datos(libro.get('autores', [''])[0] if isinstance(libro, dict) else libro.autor)
        key = f"{titulo_norm}|{autor_norm}"
        libro['comentarios_count'] = comentarios_por_libro.get(key, 0)

    return render(request, 'modulo/index.html', {
        'libros_destacados': libros_destacados,
        'resultados': resultados,
        'query': query,
        'libros_guardados': libros_guardados,
    })

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        print("DATOS RECIBIDOS POR POST (CON PERFIL):")
        print(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)  # Descomenta la creación del perfil
            messages.success(request, 'Usuario registrado con éxito (CON PERFIL). Ahora puedes iniciar sesión.')
            return redirect('login')
        else:
            print("ERRORES DEL REGISTRO USUARIO FORM (CON PERFIL):")
            print(form.errors)
            return render(request, 'modulo/registro.html', {'form': form})
    else:
        form = RegistroUsuarioForm()

    return render(request, 'modulo/registro.html', {'form': form})
@require_POST
@login_required
def guardar_libro(request):
    titulo = request.POST.get('titulo')
    autor = request.POST.get('autor')
    link = request.POST.get('link')
    portada_url = request.POST.get('portada')

    
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
            pass  

    
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
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Inicialización fuera del POST para evitar resetear formularios
    form_perfil = EditarPerfilForm(instance=user_profile)
    form_foto = EditarFotoForm(instance=user_profile)
    form_password = PasswordChangeForm(request.user)  # Formulario inicial vacío

    if request.method == 'POST':
        # Determinar qué formulario se envió
        if 'editar_perfil' in request.POST:
            form_perfil = EditarPerfilForm(request.POST, instance=user_profile)
            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('perfil')

        elif 'editar_foto' in request.POST:
            form_foto = EditarFotoForm(request.POST, request.FILES, instance=user_profile)
            if form_foto.is_valid():
                form_foto.save()
                messages.success(request, 'Foto de perfil actualizada exitosamente.')
                return redirect('perfil')

        elif 'cambiar_password' in request.POST:
            form_password = PasswordChangeForm(request.user, request.POST)  # Formulario con datos POST
            if form_password.is_valid():
                user = form_password.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Contraseña cambiada exitosamente.')
                return redirect('perfil')
            else:
                messages.error(request, 'No se pudo cambiar la contraseña. Por favor, verifica los errores.')
                # No hacemos redirect para mantener los errores

    context = {
        'form_perfil': form_perfil,
        'form_foto': form_foto,
        'form_password': form_password,
    }
    return render(request, 'modulo/perfil.html', context)

@login_required
def libros_guardados(request):
    favoritos_qs = LibroFavorito.objects.filter(usuario=request.user).order_by('-guardado_en')
    favoritos = list(favoritos_qs)

    comentarios_por_libro = defaultdict(int)
    for comentario in ComentarioExterno.objects.all():
        titulo_norm = normalizar_datos(comentario.titulo)
        autor_norm = normalizar_datos(comentario.autor.split(',')[0])
        key = f"{titulo_norm}|{autor_norm}"
        comentarios_por_libro[key] += 1

    for libro in favoritos:
        titulo_norm = normalizar_datos(libro.titulo)
        autor_norm = normalizar_datos(libro.autor.split(',')[0])
        key = f"{titulo_norm}|{autor_norm}"
        libro.num_comentarios = comentarios_por_libro.get(key, 0)

    context = {
        'favoritos': favoritos,
    }
    return render(request, 'modulo/libros_guardados.html', context)

@login_required
def libros_creados(request):
    libros_usuario = Libro.objects.filter(usuario_creador=request.user).order_by('-fecha_creacion_usuario')
    context = {
        'libros_usuario': libros_usuario,
    }
    return render(request, 'modulo/libros_creados.html', context)

@login_required
def crear_libro(request):
    categorias = Categoria.objects.all() 

    if request.method == 'POST' and 'agregar_libro' in request.POST:
        agregar_libro_form = AgregarLibroUsuarioForm(request.POST, request.FILES)
        if agregar_libro_form.is_valid():
            nuevo_libro = agregar_libro_form.save(commit=False)
            nuevo_libro.usuario_creador = request.user
            nuevo_libro.creado_por_usuario = True
            nuevo_libro.slug_titulo = slugify(nuevo_libro.titulo)
            nuevo_libro.slug_autor = slugify(nuevo_libro.autor) if nuevo_libro.autor else 'anonimo'
            nuevo_libro.save()
            messages.success(request, 'Libro añadido exitosamente.')
            return redirect('libros_creados') 
        else:
            agregar_libro_form = AgregarLibroUsuarioForm(request.POST, request.FILES) 
    else:
        agregar_libro_form = AgregarLibroUsuarioForm() 

    context = {
        'agregar_libro_form': agregar_libro_form,
        'categorias': categorias, 
    }
    return render(request, 'modulo/crear_libro.html', context)

@login_required
def historial(request):
    historial_busqueda = HistorialBusqueda.objects.filter(usuario=request.user).order_by('-fecha')
    historial_vistos = LibroVisto.objects.filter(usuario=request.user).order_by('-fecha_visto')
    context = {
        'historial_busqueda': historial_busqueda,
        'historial_vistos': historial_vistos,
    }
    return render(request, 'modulo/historial.html', context)

@login_required
def marcar_libro_visto(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor')
        link = request.POST.get('link')
        portada = request.POST.get('portada')

        try:
            libro_visto = LibroVisto.objects.get(usuario=request.user, titulo=titulo, autor=autor)
            
            libro_visto.fecha_visto = timezone.now()
            libro_visto.save()
        except LibroVisto.DoesNotExist:
            
            LibroVisto.objects.create(
                usuario=request.user,
                titulo=titulo,
                autor=autor,
                link=link,
                portada=portada
            )
        return redirect(link)

    return redirect('index')
    
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
            'link': info.get('previewLink', '#')  
        }

   
    url_sugeridos = 'https://www.googleapis.com/books/v1/volumes?q=bestsellers'
    response_sugeridos = requests.get(url_sugeridos)
    if response_sugeridos.status_code == 200:
        data_sugeridos = response_sugeridos.json()
        for item in data_sugeridos.get('items', [])[:5]:  
            info = item.get('volumeInfo', {})
            libros_sugeridos.append({
                'titulo': info.get('title', 'Sin título'),
                'autor': ", ".join(info.get('authors', ['Desconocido'])),
                'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                'link': info.get('previewLink', '#')  
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
    
    autor_principal = autor.split(',')[0].strip()

    
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
            if page_id != "-1":  
                autor_info["biografia"] = page_data.get("extract", autor_info["biografia"])

    libros = []
    if request.user.is_authenticated:
        
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{autor_principal}"
        response_books = requests.get(google_books_url)

        if response_books.status_code == 200:
            data_books = response_books.json()
            for item in data_books.get('items', []):
                info = item.get('volumeInfo', {})
                libros.append({
                    'titulo': info.get('title', 'Sin título'),
                    'portada': info.get('imageLinks', {}).get('thumbnail', ''),
                    'link': info.get('previewLink', '#')  
                })

    return render(request, 'modulo/autor_detalle.html', {
        'autor': autor_info,
        'libros': libros,
        'mostrar_mensaje': not request.user.is_authenticated  
    })

def normalizar_datos(texto):
    """Normaliza para búsquedas: quita tildes, espacios extras, caracteres especiales"""
    if not texto:
        return ""
    texto = unidecode(texto.lower().strip())  
    texto = re.sub(r'[^\w\s]', '', texto)    
    return ' '.join(texto.split())            

def comentarios_libro(request, titulo_slug, autor_slug):
    titulo = titulo_slug.replace('-', ' ')
    autor = autor_slug.replace('-', ' ')
    
    
    titulo_norm = normalizar_datos(titulo)
    autor_norm = normalizar_datos(autor.split(',')[0])
    comentarios = ComentarioExterno.objects.filter(
        titulo__iexact=titulo,  
        autor__icontains=autor.split(',')[0].strip()  
    )

    if request.method == "POST":
        ComentarioExterno.objects.create(
            titulo=titulo,  
            autor=autor,    
            usuario=request.user,
            contenido=request.POST.get("contenido")
        )
        return redirect("comentarios_libro", 
            titulo_slug=slugify(titulo), 
            autor_slug=slugify(autor)
        )

    return render(request, "modulo/comentarios_libro.html", {
        "titulo": titulo,
        "autor": autor,
        "comentarios": comentarios,
    })


@login_required
def editar_comentario(request, comentario_id):
    comentario = get_object_or_404(ComentarioExterno, id=comentario_id)
    if request.user == comentario.usuario or request.user.is_superuser:
        if request.method == "POST":
            comentario.contenido = request.POST.get("contenido")
            comentario.save()
            messages.success(request, 'Comentario editado correctamente.')
        else:
            messages.error(request, 'Método no válido.')
    else:
        messages.error(request, 'No tienes permiso para editar este comentario.')

    return redirect("comentarios_libro",
        titulo_slug=slugify(comentario.titulo),
        autor_slug=slugify(comentario.autor)
    )

@login_required
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(ComentarioExterno, id=comentario_id)
    if request.user == comentario.usuario or request.user.is_superuser:
        if request.method == "POST":
            comentario.delete()
            messages.success(request, 'Comentario eliminado correctamente.')
        else:
            messages.error(request, 'Método no válido.')
    else:
        messages.error(request, 'No tienes permiso para eliminar este comentario.')

    return redirect("comentarios_libro",
        titulo_slug=slugify(comentario.titulo),
        autor_slug=slugify(comentario.autor)
    )