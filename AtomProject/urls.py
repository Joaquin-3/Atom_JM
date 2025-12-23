from django.contrib import admin
from django.urls import path
from mainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/editar/<id>/', views.cliente_editar, name='cliente_editar'),
    path('clientes/eliminar/<id>/', views.cliente_eliminar, name='cliente_eliminar'),
    path('registro/', views.registro),
    path('inicio/', views.inicio, name="inicio"),
    path('registro-usuario/', views.reg_usuario),
    path('ordenes/', views.ordenes_trabajo, name='ordenes_trabajo'),
    path('documentacion/', views.ordenes_historial, name='documentacion'),
    path('ordenes/crear/', views.crear_orden, name='crear_orden'),
    path('ordenes/editar/<int:pk>/', views.orden_editar, name='editar_ordenes'),
    path('', views.login, name="login")
]
