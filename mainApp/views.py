from django.shortcuts import render, redirect
from .models import Cliente, Marca, Modelo, Estado, Orden_de_Trabajo
from .forms import ClienteForm, EstadoForm
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.utils import timezone



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

def inicio(req):
    return render(req, "inicio.html")

def login(req):
    return render(req, "login.html")

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
        'query': query,
        'active_page': 'clientes',
        'form': form  
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


def cliente_eliminar(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes')

    return render(request, 'confirmar_eliminacion.html', {
        'cliente': cliente
    })

from django.db.models import Q  # ya lo tienes importado 👍



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
        marca_nombre = request.POST.get("marca", "").strip()
        modelo_nombre = request.POST.get("modelo", "").strip()
        abono_raw = request.POST.get("abono", "").strip()
        total_raw = request.POST.get("total", "").strip()
        observaciones = request.POST.get("observaciones", "").strip()

        # Validación mínima de campos
        if not cliente_id or not modelo_nombre:
            messages.error(request, "Debes completar Cliente y Modelo.")
            return redirect("ordenes_trabajo")

        total = validar_monto(total_raw, "Total", request, obligatorio=True)
        if total is None:
            return redirect("ordenes_trabajo")

        abono = validar_monto(abono_raw, "Abono", request, obligatorio=False)
        if abono is None:
            return redirect("ordenes_trabajo")

        # Obtener o crear entidades relacionadas
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, "Cliente no encontrado.")
            return redirect("ordenes_trabajo")
        
        try:
            marca = Marca.objects.get(id=marca_nombre)
        except Marca.DoesNotExist:
            messages.error(request, "Marca no encontrada.")
            return redirect("ordenes_trabajo")
        modelo, _ = Modelo.objects.get_or_create(nombre_modelo=modelo_nombre)
        estado, _ = Estado.objects.get_or_create(tipo_estado="PENDIENTE")

        # Usuario autenticado o default
        usuario = request.user if request.user.is_authenticated else User.objects.first()

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