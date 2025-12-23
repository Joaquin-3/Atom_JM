from django.shortcuts import render, redirect,get_object_or_404
from .models import Cliente, Marca, Modelo, Estado, Orden_de_Trabajo,Perfil
from .forms import ClienteForm, EstadoForm
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models.deletion import ProtectedError



@login_required
def ver_tecnicos(request):
    # 🔒 Solo administradores
    if not es_admin(request.user):
        messages.error(request, "Acceso denegado.")
        return redirect("inicio")

    # 📋 Obtener todos los usuarios del grupo Técnico
    tecnicos = User.objects.filter(groups__name="Tecnico").order_by("username")

    return render(request, "crear_tecnico.html", {
        "tecnicos": tecnicos
    })

#PARA USUARIOS 

def es_admin(user):
    return user.groups.filter(name="Administrador").exists()

def es_tecnico(user):
    return user.groups.filter(name="Tecnico").exists()

@login_required
def panel_admin(request):
    print("USUARIO:", request.user.username)
    print("GRUPOS:", request.user.groups.all())

    if not es_admin(request.user):
        messages.error(request, "Acceso denegado: solo administradores.")
        return redirect('inicio')

    return render(request, "admin_panel.html")


from django.contrib.auth.models import User, Group


CONTRASENA_TECNICO = "Tecnico123"  

from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required

@login_required
def crear_tecnico(request):
    if not es_admin(request.user):
        messages.error(request, "No tienes permisos para crear usuarios.")
        return redirect("inicio")

    if request.method == "POST":
        username = request.POST.get("username")

        if not username:
            messages.error(request, "Debes ingresar un nombre de usuario.")
            return redirect("crear_tecnico")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")
            return redirect("crear_tecnico")

        user = User.objects.create_user(
            username=username,
            password=CONTRASENA_TECNICO
        )

        grupo_tecnico, _ = Group.objects.get_or_create(name="Tecnico")
        user.groups.add(grupo_tecnico)

        # Crear perfil
        Perfil.objects.create(user=user, debe_cambiar_password=True)

        messages.success(
            request,
            f"Técnico creado. Contraseña inicial: {CONTRASENA_TECNICO}"
        )

        return redirect("crear_tecnico")  # Redirige a la misma página

    # ✅ Aquí se cargan todos los técnicos
    grupo_tecnico = Group.objects.get(name="Tecnico")
    tecnicos = grupo_tecnico.user_set.all()

    return render(request, "crear_tecnico.html", {
        "tecnicos": tecnicos
    })



from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def cambiar_password(request):

    # 🔒 Si NO es técnico, no entra aquí
    if not es_tecnico(request.user):
        return redirect("inicio")

    # ✅ Si ya cambió la contraseña, no vuelve aquí
    if request.user.last_login is not None:
        return redirect("inicio")

    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("cambiar_password")

        if len(password1) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return redirect("cambiar_password")

        request.user.set_password(password1)
        request.user.save()

        # 🔑 Mantiene la sesión activa
        update_session_auth_hash(request, request.user)

        messages.success(request, "Contraseña actualizada correctamente.")
        return redirect("inicio")

    return render(request, "cambiar_password.html")





# Límite lógico para montos
MAX_MONTO = Decimal("9999999.99")  # 9.999.999,99

def validar_monto(valor_str, nombre_campo, request, obligatorio=True):
    """
    Convierte el valor a Decimal y valida:
    - que sea número
    - que no sea negativo
    - que no supere MAX_MONTO
    Devuelve un Decimal válido o None si hay error (y deja un messages.error).
    """
    texto = (valor_str or "").strip()

    if not texto:
        if obligatorio:
            messages.error(request, f"{nombre_campo} es obligatorio.")
            return None
        else:
            return Decimal("0")

    try:
        valor = Decimal(texto)
    except InvalidOperation:
        messages.error(request, f"{nombre_campo} debe ser un número válido.")
        return None

    if valor < 0:
        messages.error(request, f"{nombre_campo} no puede ser negativo.")
        return None

    if valor > MAX_MONTO:
        messages.error(
            request,
            f"{nombre_campo} no puede ser mayor que 9.999.999,99."
        )
        return None

    return valor



# Create your views here.
def registro(req):
    return render(req, "registro.html")


def obtener_perfil(user):
    perfil, creado = Perfil.objects.get_or_create(user=user)
    return perfil

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            auth_login(request, user)

            perfil = obtener_perfil(user)

            if es_tecnico(user) and perfil.debe_cambiar_password:
                return redirect("cambiar_password")

            return redirect("inicio")

        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "login.html")



@login_required
def cambiar_password(request):

    if not es_tecnico(request.user):
        return redirect("inicio")

    perfil = obtener_perfil(request.user)

    # 🔒 Si ya cambió contraseña → fuera
    if not perfil.debe_cambiar_password:
        return redirect("inicio")

    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("cambiar_password")

        if len(password1) < 8:
            messages.error(request, "Mínimo 8 caracteres.")
            return redirect("cambiar_password")

        request.user.set_password(password1)
        request.user.save()

        # 🔥 MARCAR COMO COMPLETADO
        perfil.debe_cambiar_password = False
        perfil.save()

        update_session_auth_hash(request, request.user)

        messages.success(request, "Contraseña actualizada.")
        return redirect("inicio")

    return render(request, "cambiar_password.html")



@login_required
def inicio(request):

    if es_tecnico(request.user) and request.user.last_login is None:
        return redirect("cambiar_password")

    return render(request, "inicio.html")



def reg_usuario(req):
    return render(req, "registro_usuario.html")


def clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST) 
        if form.is_valid(): 
            form.save() 
            return redirect('clientes')
    else:
        form = ClienteForm() 

    query = request.GET.get('search', '')
    if query:
        clientes = Cliente.objects.filter(
            Q(nombre__icontains=query) |
            Q(rut__icontains=query) |
            Q(telefono__icontains=query) |
            Q(correo__icontains=query)
        )
    else:
        clientes = Cliente.objects.all()

    return render(request, 'clientes.html', {
        'clientes': clientes,
        'form': form,
        'es_tecnico': es_tecnico(request.user),   # ✅ AQUÍ
    })


def cliente_editar(request, id):

    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
  
        form = ClienteForm(request.POST, instance=cliente)
        
        if form.is_valid():
            form.save() 
            return redirect('clientes')
        

    else:
  
        form = ClienteForm(instance=cliente)

    return render(request, 'editar_cliente.html', {
        'form': form,   
        'cliente': cliente 
    })


@login_required
def cliente_eliminar(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    # Solo admins pueden entrar a esta vista
    if not es_admin(request.user):
        messages.error(request, "No tienes permisos para eliminar clientes.")
        return redirect('clientes')

    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, "Cliente eliminado correctamente.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el cliente porque tiene órdenes de trabajo asociadas."
            )
        return redirect('clientes')

    return render(request, 'confirmar_eliminacion.html', {'cliente': cliente})




# ÓRDENES DE TRABAJO

def ordenes_trabajo(request):

    Estado.objects.get_or_create(tipo_estado="PENDIENTE")
    Estado.objects.get_or_create(tipo_estado="FINALIZADO")

    # Texto del buscador
    q = request.GET.get("q", "").strip()

    # Orden (chips)
    order = request.GET.get("order", "")      # dispositivo, marca, cliente, total, fecha
    sort = request.GET.get("sort", "desc")    # asc / desc

    # Base queryset
    ordenes = (
        Orden_de_Trabajo.objects
        .select_related("cliente", "marca", "modelo", "estado")
        .all()
    )

    # FILTRO DE BÚSQUEDA
    if q:
        ordenes = ordenes.filter(
            Q(cliente__nombre__icontains=q) |
            Q(marca__nombre_marca__icontains=q) |
            Q(modelo__nombre_modelo__icontains=q) |
            Q(observaciones__icontains=q)
        )

    # ORDENAMIENTO SEGÚN CHIP
    order_map = {
        "numero": "numero_control",
        "cliente": "cliente__nombre",
        "marca": "marca__nombre_marca",
        "total": "total_pagar",
        "fecha": "fecha",
        # "device": "lo_que_sea_si_más_adelante_tienes_dispositivo"
        "device": "numero_control",   # <-- NUEVO: para que el chip Dispositivo ordene por N° de órden
    }

    order_field = order_map.get(order, "fecha")  # por defecto, fecha

    if sort == "desc":
        order_field = "-" + order_field

    ordenes = ordenes.order_by(order_field)

    clientes = Cliente.objects.all()
    marcas = Marca.objects.all()
   

    return render(request, "ordenes_trabajo.html", {
        "ordenes": ordenes,
        "clientes": clientes,
        "marcas": marcas,
        "q": q,             # <-- NUEVO (para que el buscador mantenga el texto)
        "order": order,     # <-- NUEVO (para saber qué chip está activo)
        "sort": sort,       # <-- NUEVO (para que Asc/Desc funcionen bien)
    })


def ordenes_historial(request):
    """
    MISMA LÓGICA que ordenes_trabajo,
    pero renderiza OTRO template: documentacion_ordenes.html
    """
    query = request.GET.get("q", "").strip()
    order = request.GET.get("order", "fecha")
    sort = request.GET.get("sort", "desc")

    ordenes = Orden_de_Trabajo.objects.all()

    if query:
        ordenes = ordenes.filter(
            Q(cliente__nombre__icontains=query) |
            Q(marca__nombre_marca__icontains=query) |
            Q(modelo__nombre_modelo__icontains=query)
        )

    mapping = {
        "numero": "numero_control",          # <-- NUEVO: para N° de órden
        "device": "numero_control",          # <-- NUEVO: si usas ?order=device en los chips
        "cliente": "cliente__nombre",
        "marca": "marca__nombre_marca",
        "total": "total_pagar",
        "fecha": "fecha",
    }
    campo = mapping.get(order, "fecha")
    if sort == "asc":
        ordenes = ordenes.order_by(campo)
    else:
        ordenes = ordenes.order_by("-" + campo)

  
    return render(request, "documentacion.html", {
        "ordenes": ordenes,
        "query": query,
        "order": order,
        "sort": sort,
    })

def crear_orden(request):
    if request.method == "POST":
        cliente_id = request.POST.get("cliente", "").strip()
        marca_id = request.POST.get("marca", "").strip()
        modelo_nombre = request.POST.get("modelo", "").strip()
        abono_raw = request.POST.get("abono", "").strip()
        total_raw = request.POST.get("total", "").strip()
        observaciones = request.POST.get("observaciones", "").strip()

        # Validación mínima de campos
        if not cliente_id or not modelo_nombre:
            messages.error(request, "Debes completar Cliente y Modelo.")
            return redirect("ordenes_trabajo")

        # Convertir total a Decimal
        try:
            total = Decimal(total_raw)
            if total <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "El total ingresado no es válido.")
            return redirect("ordenes_trabajo")

        # Convertir abono a Decimal (opcional)
        abono = Decimal(0)
        if abono_raw:
            try:
                abono = Decimal(abono_raw)
                if abono < 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                messages.error(request, "El abono ingresado no es válido.")
                return redirect("ordenes_trabajo")

        # Validación: abono no puede ser mayor que el total
        if abono > total:
            messages.error(request, "El abono no puede ser mayor que el total a pagar.")
            return redirect("ordenes_trabajo")

        # Obtener cliente
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, "Cliente no encontrado.")
            return redirect("ordenes_trabajo")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al obtener el cliente: {e}")
            return redirect("ordenes_trabajo")

        # Obtener marca
        try:
            marca = Marca.objects.get(id=marca_id)
        except Marca.DoesNotExist:
            messages.error(request, "Marca no encontrada.")
            return redirect("ordenes_trabajo")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al obtener la marca: {e}")
            return redirect("ordenes_trabajo")

        # Obtener o crear modelo y estado
        try:
            modelo, _ = Modelo.objects.get_or_create(nombre_modelo=modelo_nombre)
            estado, _ = Estado.objects.get_or_create(tipo_estado="PENDIENTE")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al crear modelo o estado: {e}")
            return redirect("ordenes_trabajo")

        # Usuario autenticado o default
        usuario = request.user if request.user.is_authenticated else User.objects.first()

        # Crear la orden
        try:
            Orden_de_Trabajo.objects.create(
                cliente=cliente,
                usuario=usuario,
                estado=estado,
                marca=marca,
                modelo=modelo,
                total_pagar=total,
                abono=abono,
                observaciones=observaciones,
            )
            messages.success(request, "La órden fue creada correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al crear la orden: {e}")
            return redirect("ordenes_trabajo")

        return redirect("ordenes_trabajo")

    return redirect("ordenes_trabajo")

def orden_editar(request, pk):
    orden = get_object_or_404(Orden_de_Trabajo, pk=pk)

    # 🟥 ELIMINAR
    if request.method == "POST" and "eliminar" in request.POST:
        numero = orden.numero_control
        orden.delete()
        messages.success(request, f"La órden #{numero} fue eliminada correctamente.")
        return redirect("documentacion")   # o 'ordenes_trabajo'

    # 🟩 GUARDAR CAMBIOS
    if request.method == "POST" and "guardar" in request.POST:

        # --------- CLIENTE / MARCA / MODELO ----------
        nombre_cliente = request.POST.get("cliente", "").strip()
        if nombre_cliente:
            orden.cliente.nombre = nombre_cliente
            orden.cliente.save()

        nombre_marca = request.POST.get("marca", "").strip()
        if nombre_marca:
            orden.marca.nombre_marca = nombre_marca
            orden.marca.save()

        nombre_modelo = request.POST.get("modelo", "").strip()
        if nombre_modelo:
            orden.modelo.nombre_modelo = nombre_modelo
            orden.modelo.save()

        # --------- FECHA ----------
        fecha_raw = request.POST.get("fecha", "").strip()

        if fecha_raw:
            # viene algo desde el input type="date"
            fecha_parsed = parse_date(fecha_raw)  # espera formato YYYY-MM-DD
            if not fecha_parsed:
                messages.error(request, "Fecha inválida.")
                return redirect("editar_ordenes", pk=orden.pk)

            # si tu campo fecha es DateField, esto va perfecto
            # si es DateTimeField, también funciona (Django se queda con la fecha)
            orden.fecha = fecha_parsed
        else:
            # si el usuario deja vacío y en la BD tampoco hay fecha → ponemos una por defecto
            if not orden.fecha:
                orden.fecha = timezone.now()

        # --------- TOTAL / ABONO ----------
        total_actual = orden.total_pagar
        abono_actual = orden.abono if orden.abono is not None else Decimal("0")

        total_raw = request.POST.get("total", "").strip()
        abono_raw = request.POST.get("abono", "").strip()

        nuevo_total = total_actual
        nuevo_abono = abono_actual
        cambio_montos = False

        if total_raw != "":
            try:
                nuevo_total = Decimal(total_raw)
                cambio_montos = True
            except InvalidOperation:
                messages.error(request, "Total inválido.")
                return redirect("editar_ordenes", pk=orden.pk)

        if abono_raw != "":
            try:
                nuevo_abono = Decimal(abono_raw)
                cambio_montos = True
            except InvalidOperation:
                messages.error(request, "Abono inválido.")
                return redirect("editar_ordenes", pk=orden.pk)

        # ✅ SOLO validamos si el usuario tocó montos
        if cambio_montos:
            if nuevo_total <= 0:
                messages.error(request, "El total debe ser mayor que 0.")
                return redirect("editar_ordenes", pk=orden.pk)

            if nuevo_abono < 0:
                messages.error(request, "El abono no puede ser negativo.")
                return redirect("editar_ordenes", pk=orden.pk)

            if nuevo_abono > nuevo_total:
                messages.error(request, "El abono no puede ser mayor que el total.")
                return redirect("editar_ordenes", pk=orden.pk)

            LIMITE = Decimal("9999999.99")
            if nuevo_total > LIMITE or nuevo_abono > LIMITE:
                messages.error(
                    request,
                    "Monto demasiado grande (máximo 9.999.999,99)."
                )
                return redirect("editar_ordenes", pk=orden.pk)

        orden.total_pagar = nuevo_total
        orden.abono = nuevo_abono

        # --------- OBSERVACIONES ----------
        orden.observaciones = request.POST.get("observaciones", "").strip()

        # --------- ESTADO ----------
        estado_id = request.POST.get("estado")
        if estado_id:
            try:
                orden.estado = Estado.objects.get(id=estado_id)
                orden.estado = orden.estado
            except Estado.DoesNotExist:
                pass

        orden.save()
        messages.success(
            request,
            f"La órden #{orden.numero_control} fue actualizada correctamente."
        )
        return redirect("documentacion")   # o 'ordenes_trabajo'

    estados = Estado.objects.all()
    return render(request, "editar_ordenes.html", {
        "orden": orden,
        "estados": estados,
    })