from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('detalle_producto/<str:Nombre>/', views.detalle_producto, name="detalle_producto"),
    path('carrito/', views.carrito, name="carrito"),
    path('iniciar_sesion/', views.iniciar_sesion, name="iniciar_sesion"),
    path('perfil_usuario/<str:nombre_de_usuario>/', views.perfil_usuario, name='perfil_usuario'),
    path('registrar_cliente/', views.registrar_cliente, name='registrar_cliente'),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('historial_pedidos/', views.historial_pedidos, name="historial_pedidos"),
    path('editar_perfil/<str:nombre_de_usuario>/', views.editar_perfil, name="editar_perfil"),
    path('mostrar_productos/<str:categoria>/', views.mostrar_productos, name='mostrar_productos'),
    path('agregar_al_carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('actualizar-carrito/', views.actualizar_carrito, name='actualizar_carrito'),
    path('comprar_productos/', views.comprar_productos, name='comprar_productos'),
    path('PoliticaPrivacidad/', views.PoliticaPrivacidad, name='PoliticaPrivacidad'),
    path('TerminosCondiciones/', views.TerminosCondiciones, name='TerminosCondiciones'),
    path('final_compra/', views.final_compra, name='final_compra'),
    path('generar_factura_pdf/', views.generar_factura_pdf, name='generar_factura_pdf'),
    path('generar_ticket_pdf/', views.generar_ticket_pdf, name='generar_ticket_pdf')
]