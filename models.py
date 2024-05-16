from django.db import models

# Create your models here.
class Producto(models.Model):
    Nombre = models.CharField(max_length=100)
    ImagenProducto = models.ImageField(upload_to='product_images/', blank=True, null=True)
    Descripcion = models.TextField()
    Precio = models.DecimalField(max_digits=10, decimal_places=2)
    Categoria = models.CharField(max_length=100, default="Otro")
    Cantidad_en_stock = models.IntegerField(default=0)

    def __str__(self):
        return self.Nombre

    def reducir_stock(self, cantidad):
        self.cantidad_en_stock -= cantidad
        self.save()

    def aumentar_stock(self, cantidad):
        self.cantidad_en_stock += cantidad
        self.save()

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15)
    password = models.CharField(max_length=128,default='1234')
    direccion = models.TextField()

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    productos = models.ManyToManyField('Producto', through='ItemPedido')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Información de la tarjeta del cliente
    numero_tarjeta = models.CharField(max_length=16)  # El número de la tarjeta (generalmente 16 dígitos)
    fecha_vencimiento = models.DateField(null=True)  # La fecha de vencimiento de la tarjeta
    nombre_titular = models.CharField(max_length=100,null=True)  # El nombre del titular de la tarjeta

    # Dirección de envío
    direccion_envio = models.TextField(default='Dirección predeterminada')  # La dirección a la que se enviarán los productos

    def __str__(self):
        return f'Pedido {self.id} - Cliente: {self.cliente.nombre}'

class ItemPedido(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Producto: {self.producto.Nombre} - Cantidad: {self.cantidad}'

class SeguimientoPedido(models.Model):
    ESTADOS = (
        ('Pendiente', 'Pendiente'),
        ('En camino', 'En camino'),
        ('Entregado', 'Entregado'),
    )
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='seguimiento')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Seguimiento Pedido {self.pedido.id} - Estado: {self.estado}'