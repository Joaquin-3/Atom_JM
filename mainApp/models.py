from django.db import models
from django.utils.safestring import mark_safe
from django.utils import timezone  
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# Create your models here.
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Estado(models.Model):
    
    Estados = [
        ('PENDIENTE', 'Pendiente'),
        ('FINALIZADO', 'Finalizado'),
    ]
    
    tipo_estado = models.CharField(max_length=30, choices=Estados, default='PENDIENTE')
    def __str__(self):
        return self.tipo_estado
    
    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

        
class Marca(models.Model):
    nombre_marca = models.CharField(max_length=20)
    img_marca = models.ImageField(upload_to="marcas", blank=True, null=True)

    def __str__(self):
        return self.nombre_marca

    def imagen_preview(self):
        if self.img_marca:
            return mark_safe(f'<img src="{self.img_marca.url}" width="80" height="auto" />')
        return "Sin imagen"
    imagen_preview.short_description = "Logo"

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

        
class Modelo(models.Model):
    nombre_modelo = models.CharField(max_length=20, blank=False)

    def __str__(self):
        return self.nombre_modelo
    
    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"



class Orden_de_Trabajo(models.Model):
    numero_control = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    total_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    abono = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha = models.DateField(default=timezone.now)
    observaciones = models.CharField(max_length=200, null=True, blank=True)

    @property
    def saldo(self):
        return self.total_pagar - (self.abono or 0)

    def clean(self):
        super().clean()
        if self.abono and self.abono > self.total_pagar:
            raise ValidationError({'abono': "El abono no puede ser mayor que el total a pagar."})

    def __str__(self):
        return f"Orden {self.numero_control} - {self.cliente.nombre}"
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    debe_cambiar_password = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"
