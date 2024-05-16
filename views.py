from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import Cliente, Producto, Pedido, SeguimientoPedido, ItemPedido
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q
from django.db import transaction
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
from django.conf import settings
from reportlab.lib.utils import ImageReader
from PIL import Image

# Create your views here.
def index(request):
    query = request.GET.get('producto')
    productos = Producto.objects.all()  # Obtener todos los eventos por defecto
    num_productos_en_carrito = 0  # Definir la variable con un valor inicial

    if query:  # Si hay una consulta de búsqueda
        productos = Producto.objects.filter(Nombre__icontains=query)

    # Verificar si el usuario existe en la base de datos
    user_exists = False
    cliente_nombre = None
    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass

    if 'carrito' in request.session:
        carrito = request.session['carrito']
        num_productos_en_carrito = len(carrito.keys())

    return render(request, 'index.html', {
        'productos': productos,
        'user_exists': user_exists,
        'cliente_nombre': cliente_nombre,
        'num_productos_en_carrito': num_productos_en_carrito,
    })

def detalle_producto(request,Nombre):
    producto = Producto.objects.get(Nombre=Nombre)
    num_productos_en_carrito = 0  # Definir la variable con un valor inicial

    # Verificar si el usuario existe en la base de datos
    user_exists = False
    cliente_nombre = None
    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass
    if 'carrito' in request.session:
        carrito = request.session['carrito']
        num_productos_en_carrito = len(carrito.keys())

    context = {
        'producto': producto,
        'user_exists': user_exists,
        'cliente_nombre': cliente_nombre,
        'num_productos_en_carrito': num_productos_en_carrito,
    }
    return render(request, 'detalle_producto.html', context)

def carrito(request):
    user_exists = False
    cliente_nombre = None
    total_price = 0  # Inicializar el precio total
    productos_en_carrito = []  # Lista de tuplas (nombre_producto, precio_producto, cantidad_producto)

    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass

    # Manejar la lógica para eliminar productos del carrito
    if request.method == 'POST':
        eliminar_producto = request.POST.get('eliminar_producto')
        if eliminar_producto:
            carrito = request.session.get('carrito', {})
            if eliminar_producto in carrito:
                del carrito[eliminar_producto]
                request.session['carrito'] = carrito

    # Obtener el conjunto de nombres de productos únicos
    carrito = request.session.get('carrito', {})
    productos_unicos_en_carrito = set(carrito.keys())

    # Calcular el precio total de los productos en el carrito
    for nombre_producto in productos_unicos_en_carrito:
        producto = Producto.objects.get(Nombre=nombre_producto)
        cantidad = carrito[nombre_producto]
        precio_producto = producto.Precio
        categoria = producto.Categoria
        total_price += precio_producto * cantidad
        productos_en_carrito.append((nombre_producto, precio_producto, cantidad, categoria))

    # Obtener el número total de productos en el carrito
    num_productos_en_carrito = len(productos_unicos_en_carrito)

    return render(request, "carrito.html", {
        'user_exists': user_exists,
        'cliente_nombre': cliente_nombre,
        'total_price': total_price,
        'productos_en_carrito': productos_en_carrito,
        'num_productos_en_carrito': num_productos_en_carrito,
    })

def actualizar_carrito(request):
    if request.method == 'POST':
        producto = request.POST.get('producto')
        nueva_cantidad = int(request.POST.get('nueva_cantidad', 0))

        # Verifica si la nueva cantidad es válida
        if nueva_cantidad > 0:
            carrito = request.session.get('carrito', {})
            carrito[producto] = nueva_cantidad
            request.session['carrito'] = carrito

    return redirect('carrito')

def iniciar_sesion(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            cliente = Cliente.objects.get(email=email)
            if cliente.password == password:
                # Almacenar el correo electrónico del usuario en la sesión
                request.session['user_email'] = email
                # Las contraseñas coinciden, redirigir al usuario a la página de inicio
                return redirect('index')
            else:
                # Las contraseñas no coinciden, mostrar un mensaje de error
                mensaje = "La contraseña no es correcta."
                return render(request, 'iniciar_sesion.html', {'mensaje': mensaje})
        except Cliente.DoesNotExist:
            # No se encontró ningún cliente con ese correo, mostrar un mensaje de error
            mensaje = "No se encontró ninguna cuenta asociada a ese correo."
            return render(request, 'iniciar_sesion.html', {'mensaje': mensaje})

    return render(request, 'iniciar_sesion.html')

def registrar_cliente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        password = request.POST.get('password')
        confirmar_password = request.POST.get('confirmarPassword')

        # Verificar si las contraseñas coinciden
        if password != confirmar_password:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('iniciar_sesion')  # Reemplaza 'nombre_de_la_url_de_registro' por el nombre de la URL de tu página de registro

        # Crear un nuevo cliente y guardarlo en la base de datos
        nuevo_cliente = Cliente(nombre=nombre, email=email, telefono=telefono, direccion=direccion, password=password)
        nuevo_cliente.save()

        # Establecer user_exists en True después del registro exitoso
        request.session['user_email'] = email

        messages.success(request, '¡Registro exitoso! Por favor, inicia sesión.')

        return redirect('index')  # Reemplaza 'nombre_de_la_url_de_inicio_de_sesion' por el nombre de la URL de tu página de inicio de sesión

    return render(request, 'iniciar_sesion.html')

def perfil_usuario(request, nombre_de_usuario):
    cliente = get_object_or_404(Cliente, nombre=nombre_de_usuario)  # Obtén el cliente desde la base de datos

    context = {
        'cliente': cliente
    }

    return render(request, 'perfil_usuario.html', context)

def historial_pedidos(request):
    user_email = request.session.get('user_email')  # Obtener el correo electrónico del usuario de la sesión
    if user_email:
        try:
            cliente = Cliente.objects.get(email=user_email)  # Obtener el cliente asociado al correo electrónico
            pedidos = Pedido.objects.filter(cliente=cliente)  # Filtrar los pedidos del cliente
            return render(request, 'historial_pedidos.html', {'pedidos': pedidos})
        except Cliente.DoesNotExist:
            # Manejar el caso en el que el cliente no exista
            pass

    # Redirigir al usuario a la página de inicio de sesión si no hay correo electrónico en la sesión o el cliente no existe
    return redirect('perfil_usuario')

def editar_perfil(request, nombre_de_usuario):
    cliente = Cliente.objects.get(nombre=nombre_de_usuario)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        password = request.POST.get('password')

        # Obtener el objeto de cliente actual
        cliente = Cliente.objects.get(email=request.session['user_email'])

        # Actualizar los campos del cliente con los nuevos valores
        cliente.nombre = nombre
        cliente.email = email
        cliente.telefono = telefono
        cliente.direccion = direccion
        cliente.password = password
        cliente.save()

        # Redirigir al usuario a la página de perfil
        return redirect('perfil_usuario', nombre_de_usuario=cliente.nombre)

    return render(request, 'editar_perfil.html', {'cliente': cliente})

def cerrar_sesion(request):
    logout(request)
    return redirect('index')

def mostrar_productos(request, categoria=None):
    user_exists = False
    cliente_nombre = None
    num_productos_en_carrito = 0  # Definir la variable con un valor inicial
    
    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass
    
    if 'carrito' in request.session:
        carrito = request.session['carrito']
        num_productos_en_carrito = len(carrito.keys())

    # Obtener el nombre del producto de la consulta GET
    nombre_producto = request.GET.get('producto', '')

    # Filtrar los productos por categoría y nombre (si se proporciona)
    productos = Producto.objects.all()
    if categoria:
        productos = productos.filter(Categoria=categoria)
    if nombre_producto:
        productos = productos.filter(Nombre__icontains=nombre_producto)

    return render(request, "mostrar_productos.html", {'user_exists': user_exists, 'cliente_nombre': cliente_nombre, 'productos': productos,'categoria': categoria, 'num_productos_en_carrito': num_productos_en_carrito,})

def agregar_al_carrito(request):
    if request.method == 'POST':
        nombre_producto = request.POST.get('nombre_producto')
        cantidad = int(request.POST.get('cantidad', 1))
        producto = Producto.objects.get(Nombre=nombre_producto)
        
        # Agrega el producto al carrito (puedes implementar esta lógica según tus necesidades)
        carrito = request.session.get('carrito', {})
        if nombre_producto in carrito:
            carrito[nombre_producto] += cantidad
        else:
            carrito[nombre_producto] = cantidad
        
        request.session['carrito'] = carrito

        return redirect('carrito')  # Redirige a la vista del carrito

    return redirect('index')  # Si no se envía una solicitud POST, redirige a la página principal o a donde desees

def comprar_productos(request):
    user_exists = False
    cliente_nombre = None
    total_price = 0  # Inicializar el precio total
    productos_en_carrito = []  # Lista de tuplas (nombre_producto, precio_producto, cantidad_producto)

    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass

    # Calcular el precio total de los productos en el carrito
    carrito = request.session.get('carrito', {})
    if carrito:
        for nombre_producto, cantidad in carrito.items():
            producto = Producto.objects.get(Nombre=nombre_producto)
            precio_producto = producto.Precio
            categoria = producto.Categoria
            total_price += precio_producto * cantidad
            productos_en_carrito.append((nombre_producto, float(precio_producto), cantidad, categoria))  # Convertir a flotante

    if request.method == 'POST':
        form_data = request.POST

        # Capturar los datos del formulario...
        nombre_titular = form_data.get('nombre-tarjeta')
        numero_tarjeta = form_data.get('numero-tarjeta')
        fecha_expiracion_tarjeta = form_data.get('fecha-expiracion')
        if fecha_expiracion_tarjeta:
            fecha_expiracion_tarjeta = datetime.strptime(fecha_expiracion_tarjeta, '%m/%y')
        direccion_envio = form_data.get('direccion-envio')

        # Crear el objeto Pedido y guardarlo en la base de datos
        with transaction.atomic():
            pedido = Pedido.objects.create(
                cliente=cliente,
                total=total_price,
                numero_tarjeta=numero_tarjeta,
                fecha_vencimiento=fecha_expiracion_tarjeta,
                nombre_titular=nombre_titular,
                direccion_envio=direccion_envio
            )
            
            # Crear un registro de seguimiento del pedido
            seguimiento = SeguimientoPedido.objects.create(
                pedido=pedido,
                estado='Pendiente'
            )

            # Agregar los productos al pedido
            for nombre_producto, cantidad in carrito.items():
                producto = Producto.objects.get(Nombre=nombre_producto)
                precio_unitario = producto.Precio
                ItemPedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )
                
                # Reducir la cantidad en stock del producto
                producto.Cantidad_en_stock -= cantidad
                producto.save()

            # Limpiar el carrito de la sesión
            request.session['carrito'] = {}
            
            # Almacenar los productos en el carrito y detalles del pago en la sesión
            request.session['productos_en_carrito'] = productos_en_carrito
            request.session['numero_tarjeta'] = numero_tarjeta[-4:]  # Solo guardar los últimos 4 dígitos para seguridad
            request.session['nombre_titular'] = nombre_titular
            request.session['fecha_expiracion_tarjeta'] = fecha_expiracion_tarjeta.strftime('%m/%y')

            # Redirigir a la página de confirmación de compra
            return redirect('final_compra')

    # Renderizar el formulario para realizar la compra
    return render(request, "comprar_productos.html", {'user_exists': user_exists, 'cliente_nombre': cliente_nombre, 'total_price': total_price, 'productos_en_carrito': productos_en_carrito})

def final_compra(request):
    user_exists = False
    cliente_nombre = None
    productos_en_pedido = request.session.get('productos_en_carrito', [])  # Usar 'productos_en_carrito'
    total_price = sum([precio * cantidad for _, precio, cantidad, categoria in productos_en_pedido])

    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass

    return render(request, "final_compra.html", {'user_exists': user_exists, 'cliente_nombre': cliente_nombre, 'productos_en_pedido': productos_en_pedido, 'total_price': total_price})

def TerminosCondiciones(request):
    user_exists = False
    cliente_nombre = None
    num_productos_en_carrito = 0  # Definir la variable con un valor inicial
    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass
        
    if 'carrito' in request.session:
        carrito = request.session['carrito']
        num_productos_en_carrito = len(carrito.keys())


    return render(request,"TerminosCondiciones.html", {'user_exists': user_exists, 'cliente_nombre': cliente_nombre, 'num_productos_en_carrito': num_productos_en_carrito,})

def PoliticaPrivacidad(request):
    user_exists = False
    cliente_nombre = None
    num_productos_en_carrito = 0  # Definir la variable con un valor inicial
    if 'user_email' in request.session:
        try:
            cliente = Cliente.objects.get(email=request.session['user_email'])
            user_exists = True
            cliente_nombre = cliente.nombre
        except Cliente.DoesNotExist:
            pass
    
    if 'carrito' in request.session:
        carrito = request.session['carrito']
        num_productos_en_carrito = len(carrito.keys())


    return render(request,"PoliticaPrivacidad.html", {'user_exists': user_exists, 'cliente_nombre': cliente_nombre, 'num_productos_en_carrito': num_productos_en_carrito,})

def generar_factura_pdf(request):
    # Obtener datos del formulario
    nombre = request.GET.get('nombre', '')
    rfc = request.GET.get('rfc', '')
    direccion = request.GET.get('direccion', '')
    ciudad = request.GET.get('ciudad', '')
    codigo_postal = request.GET.get('codigo_postal', '')
    pais = request.GET.get('pais', '')
    telefono = request.GET.get('telefono', '')
    email = request.GET.get('email', '')

    # Obtener detalles del pedido
    productos_en_pedido = request.session.get('productos_en_carrito', [])  # Usar 'productos_en_carrito'
    total_price = sum([precio * cantidad for _, precio, cantidad, categoria in productos_en_pedido])  # Calcular nuevamente el total_price

    fecha_actual = datetime.now().strftime("%Y-%m-%d")  # Formato: YYYY-MM-DD
    # Crear el objeto HttpResponse con el tipo MIME adecuado
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{fecha_actual}.pdf"'

    # Crear el documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Agregar contenido al PDF
    elements.append(["Factura"])
    elements.append([f"Nombre: {nombre}"])
    elements.append([f"RFC: {rfc}"])
    elements.append([f"Dirección: {direccion}"])
    elements.append([f"Ciudad: {ciudad}"])
    elements.append([f"Código Postal: {codigo_postal}"])
    elements.append([f"País: {pais}"])
    elements.append([f"Teléfono: {telefono}"])
    elements.append([f"Correo Electrónico: {email}"])
    elements.append(["Detalles del pedido:"])
    for nombre_producto, precio_producto, cantidad_producto, categoria in productos_en_pedido:
        elements.append([f"{nombre_producto}- Cantidad: {cantidad_producto}"])
    elements.append([f"Total de compra: ${total_price}"])

    # Crear la tabla con los elementos
    tabla = Table(elements, colWidths=[400], rowHeights=30)
    tabla.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    # Construir el PDF
    doc.build([tabla])  # Aquí pasamos la tabla directamente como una lista

    return response

def generar_ticket_pdf(request):
    # Obtener datos de la compra desde la sesión
    productos_en_pedido = request.session.get('productos_en_carrito', [])
    total_price = sum([precio * cantidad for _, precio, cantidad, _ in productos_en_pedido]) if productos_en_pedido else 0
    numero_tarjeta = request.session.get('numero_tarjeta', '****')
    fecha_expiracion_tarjeta = request.session.get('fecha_expiracion_tarjeta', 'No especificado')

    # Crear el PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Definir el ancho y alto del PDF
    width, height = letter

    # Cargar el logo de la empresa
    logo_path = "C:/Users/Hp/Desktop/PIA_Profesionalizacion/productos/productos/static/img/IT_SOLUTIONS.png"
    logo = ImageReader(open(logo_path, 'rb'))

    # Definir el ancho y alto de la imagen
    logo_width, logo_height = Image.open(logo_path).size

    # Calcular la posición horizontal centrada para el logo
    logo_x = (width - logo_width) / 2

    # Dibujar el logo en el PDF
    pdf.drawImage(logo, logo_x, height - 150, width=200, height=100)

    # Definir el tamaño de la fuente
    pdf.setFont("Helvetica", 12)

    # Texto para el título centrado
    title_text = "Ticket de compra"
    title_text_width = pdf.stringWidth(title_text, "Helvetica", 12)  # Obtener el ancho del texto
    title_x = (width - title_text_width) / 2  # Calcular la posición horizontal centrada

    # Dibujar el título centrado
    pdf.drawString(title_x, height - 200, title_text)

    # Datos del cliente centrados
    pdf.drawString(width / 2 - 150, height - 220, f"Número de Tarjeta: **** **** **** {numero_tarjeta}")
    pdf.drawString(width / 2 - 150, height - 240, f"Fecha de Expiración: {fecha_expiracion_tarjeta}")

    # Productos centrados
    pdf.drawString(width / 2 - 150, height - 280, "Productos:")
    y = height - 300
    if productos_en_pedido:
        for nombre_producto, precio_producto, cantidad_producto, categoria in productos_en_pedido:
            producto_text = f"{nombre_producto} - Precio: ${precio_producto:.2f} - Cantidad: {cantidad_producto}"
            producto_text_width = pdf.stringWidth(producto_text, "Helvetica", 12)
            producto_x = (width - producto_text_width) / 2
            pdf.drawString(producto_x, y, producto_text)
            y -= 20

    # Precio total centrado
    precio_total_text = f"Precio Total: ${total_price:.2f}"
    precio_total_text_width = pdf.stringWidth(precio_total_text, "Helvetica", 12)
    precio_total_x = (width - precio_total_text_width) / 2
    pdf.drawString(precio_total_x, y - 30, precio_total_text)

    # Finalizar el PDF
    pdf.showPage()
    pdf.save()

    # Obtener el contenido del buffer y crear la respuesta HTTP
    pdf_data = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ticket.pdf"'
    response.write(pdf_data)
    return response