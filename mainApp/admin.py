from django.contrib import admin
from .models import Cliente, Estado, Marca, Modelo, Orden_de_Trabajo

 # Register your models here.

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'correo')
    search_fields = ('nombre', 'rut', 'correo')

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ('tipo_estado',)
    search_fields = ('tipo_estado',)

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre_marca', 'mostrar_logo')
    search_fields = ('nombre_marca',)
    readonly_fields = ('mostrar_logo',)
    fields = ('nombre_marca', 'img_marca', 'mostrar_logo')

    @admin.display(description="Logo")
    def mostrar_logo(self, obj):
        return obj.imagen_preview()



@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ('nombre_modelo',)
    search_fields = ('nombre_modelo',)  

@admin.register(Orden_de_Trabajo)
class OrdenDeTrabajoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_control', 'cliente', 'usuario', 'estado',
        'modelo', 'marca', 'total_pagar_display', 'abono_display',
        'fecha', 'observaciones'
    )
    search_fields = (
        'numero_control', 'cliente__nombre', 'usuario__username',
        'estado__tipo_estado', 'modelo__nombre_modelo', 'marca__nombre_marca'
    )
    list_filter = ('estado', 'marca', 'modelo', 'fecha')

    @admin.display(description='Total a Pagar')
    def total_pagar_display(self, obj):
        return "CLP ${:,.0f}".format(obj.total_pagar).replace(",", ".")

    @admin.display(description='Abono ')
    def abono_display(self, obj):
        return "CLP ${:,.0f}".format(obj.abono or 0).replace(",", ".")
